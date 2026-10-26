import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.seed.seed_data import seed_database
from backend.app.models.application import Application
from backend.app.models.institution import Institution
from backend.app.models.region import Region
from backend.app.models.workflow import WorkflowStage
from backend.app.models.user import User
from backend.app.services.dashboard_service import DashboardService, CANONICAL_STAGE_CATEGORIES, STAGE_CATEGORY_MAPPING


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    return res.json()["access_token"]


def test_stage_mapping_unit_matrix():
    """
    Verifies that DashboardService.map_stage_to_category accurately maps all
    actual workflow stage keys, names, and aliases into the 6 canonical categories.
    """
    # 1. DRAFT
    for identifier in ["DRAFT", "Draft", "Draft Application", "DRAFT_APPLICATION"]:
        assert DashboardService.map_stage_to_category(identifier) == "DRAFT"

    # 2. SUBMITTED
    for identifier in ["SUBMITTED", "Submitted", "Submitted / Regional Intake", "SUBMITTED_REGIONAL"]:
        assert DashboardService.map_stage_to_category(identifier) == "SUBMITTED"

    # 3. SCRUTINY
    for identifier in [
        "UNDER_SCRUTINY", "Scrutiny in Progress", "SCRUTINY_DEFICIENT", 
        "Clarification Requested", "SCRUTINY_RECOMMENDED", "Scrutiny Cleared / Review",
        "SCRUTINY", "Scrutiny", "PENDING_CLARIFICATION", "DEFICIENCY_COMMUNICATED"
    ]:
        assert DashboardService.map_stage_to_category(identifier) == "SCRUTINY"

    # 4. EVC
    for identifier in [
        "EVC_QUEUE", "Awaiting EVC Scheduling", "EVC_SCHEDULED", 
        "EVC Inspection Scheduled", "EVC_COMPLETED", "Visit Conducted / Report Awaited",
        "EVC_REPORT_SUBMITTED", "Report Under Review", "EVC", "EVC Visit", "EVC Inspection"
    ]:
        assert DashboardService.map_stage_to_category(identifier) == "EVC"

    # 5. SAC_SHC
    for identifier in [
        "SHC_QUEUE", "Standing Hearing Committee", "SAC_APPEAL",
        "Standing Appellate Committee", "SAC_SHC", "SAC / SHC", "SAC Recommendation"
    ]:
        assert DashboardService.map_stage_to_category(identifier) == "SAC_SHC"

    # 6. DECISION (Pending statutory decision only)
    for identifier in [
        "DECISION_PENDING", "Decision Pending (Competent Auth)", 
        "DECISION", "Final Decision", "Decision Pending", "COMPETENT_AUTHORITY_QUEUE"
    ]:
        assert DashboardService.map_stage_to_category(identifier) == "DECISION"

    # Terminal states must return None (never mixed into pipeline categories)
    assert DashboardService.map_stage_to_category("APPROVED") is None
    assert DashboardService.map_stage_to_category("Approved") is None
    assert DashboardService.map_stage_to_category("REJECTED") is None
    assert DashboardService.map_stage_to_category("Rejected") is None

    # Unrecognized stages return None
    assert DashboardService.map_stage_to_category("NONEXISTENT_STAGE_XYZ") is None
    assert DashboardService.map_stage_to_category(None) is None


def test_stage_pipeline_actual_database_distribution(client: TestClient, db_session: Session):
    """
    Verifies that the National Scope (BO Officer) receives real-time, non-zero counts
    matching active database applications, with zero terminal pollution.
    """
    seed_database(db_session, generate_alerts=False)
    bo_token = get_token_for(client, "bo_officer@aicte.gov.in")

    res = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {bo_token}"})
    assert res.status_code == 200
    data = res.json()

    sb = data["stage_breakdown"]
    sd = data["stage_distribution"]
    summary = data["summary"]

    # 1. Total and active count verification
    total_db = db_session.query(Application).count()
    active_db = db_session.query(Application).filter(Application.status.notin_(["APPROVED", "REJECTED"])).count()
    assert summary["total_applications"] == total_db
    assert summary["active_applications"] == active_db

    # 2. Stage distribution consistency
    assert len(sd) == 6
    sum_distribution = sum(item["count"] for item in sd)
    assert sum_distribution == active_db, f"Expected sum of pipeline stages to equal active apps ({active_db}), got {sum_distribution}"

    # 3. Canonical stage breakdown keys verification
    canonical_keys = ["DRAFT", "SUBMITTED", "SCRUTINY", "EVC", "SAC_SHC", "DECISION"]
    sum_breakdown = sum(sb[k] for k in canonical_keys)
    assert sum_breakdown == active_db

    # 4. Verify specific non-zero counts in seeded dataset
    assert sb["SUBMITTED"] >= 1
    assert sb["SCRUTINY"] >= 4
    assert sb["EVC"] >= 6
    assert sb["SAC_SHC"] >= 2
    assert sb["DECISION"] >= 2

    # 5. Verify DECISION does NOT include approved or rejected applications
    approved_count = db_session.query(Application).filter(Application.status == "APPROVED").count()
    rejected_count = db_session.query(Application).filter(Application.status == "REJECTED").count()
    assert approved_count > 0
    assert rejected_count > 0
    # Pending decisions must be strictly less than total applications minus approved and rejected
    assert sb["DECISION"] < summary["total_applications"]
    assert sb["DECISION"] == db_session.query(Application).filter(Application.status == "DECISION_PENDING").count()


def test_stage_pipeline_scoping_isolation(client: TestClient, db_session: Session):
    """
    Verifies that stage pipeline counts are strictly scoped by region, institution,
    and assigned committee visits without cross-tenant leakage.
    """
    seed_database(db_session, generate_alerts=False)

    ro_token = get_token_for(client, "ro_north@aicte.gov.in")
    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    comm_token = get_token_for(client, "comm_member@aicte.gov.in")

    # 1. Regional Scope (RO North)
    ro_res = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {ro_token}"})
    assert ro_res.status_code == 200
    ro_data = ro_res.json()
    ro_sum = sum(item["count"] for item in ro_data["stage_distribution"])
    assert ro_sum == ro_data["summary"]["active_applications"]
    assert ro_sum < 20  # strictly less than national total

    # 2. Institutional Scope (Inst Admin)
    inst_res = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {inst_token}"})
    assert inst_res.status_code == 200
    inst_data = inst_res.json()
    inst_sum = sum(item["count"] for item in inst_data["stage_distribution"])
    assert inst_sum == inst_data["summary"]["active_applications"]
    assert inst_sum < ro_sum

    # 3. Committee Member Scope
    comm_res = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {comm_token}"})
    assert comm_res.status_code == 200
    comm_data = comm_res.json()
    comm_sum = sum(item["count"] for item in comm_data["stage_distribution"])
    assert comm_sum == comm_data["summary"]["active_applications"]
    # Committee members only see EVC or assigned stages
    assert comm_data["stage_breakdown"]["SCRUTINY"] == 0
    assert comm_data["stage_breakdown"]["EVC"] >= 1


def test_stage_pipeline_empty_dataset(client: TestClient, db_session: Session):
    """
    Verifies that when a user or scoped query returns 0 applications,
    all stage counts return 0 without errors or fabricated values.
    """
    seed_database(db_session, generate_alerts=False)
    # Create an institution admin for a brand new institution with 0 applications
    from backend.app.models.institution import Institution
    from backend.app.models.region import Region
    from backend.app.core.security import get_password_hash

    reg = db_session.query(Region).first()
    empty_inst = Institution(
        aicte_id="1-EMPTY-9999",
        name="Empty Technical College (Zero Apps)",
        region_id=reg.id,
        contact_email="empty@zero.edu.in"
    )
    db_session.add(empty_inst)
    db_session.flush()

    empty_user = User(
        email="empty_admin@zero.edu.in",
        hashed_password=get_password_hash("DemoPass@2026"),
        full_name="Empty Admin",
        role="INST_ADMIN",
        institution_id=empty_inst.id,
        region_id=reg.id,
        is_active=True
    )
    db_session.add(empty_user)
    db_session.commit()

    token = get_token_for(client, "empty_admin@zero.edu.in")
    res = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    assert data["summary"]["total_applications"] == 0
    assert data["summary"]["active_applications"] == 0
    for item in data["stage_distribution"]:
        assert item["count"] == 0
    for k in ["DRAFT", "SUBMITTED", "SCRUTINY", "EVC", "SAC_SHC", "DECISION"]:
        assert data["stage_breakdown"][k] == 0


def test_stage_pipeline_unknown_stage_handling(client: TestClient, db_session: Session):
    """
    Verifies that unexpected or unmapped workflow stages are tracked in
    unmapped diagnostics without corrupting canonical category tallies.
    """
    seed_database(db_session, generate_alerts=False)
    bo_token = get_token_for(client, "bo_officer@aicte.gov.in")

    # Add an active application with an unrecognized status and no current_stage
    inst = db_session.query(Institution).first()
    weird_app = Application(
        application_no="AICTE-TEST-UNKNOWN-99",
        institution_id=inst.id,
        region_id=inst.region_id,
        academic_year="2026-2027",
        application_type="Surprise Forensic Audit",
        route="ROUTE_A",
        status="EXPERIMENTAL_SPECIAL_INSPECTION_STAGE",
        current_stage_id=None
    )
    db_session.add(weird_app)
    db_session.commit()

    res = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {bo_token}"})
    assert res.status_code == 200
    data = res.json()

    # The unmapped application must be reported in diagnostics
    assert "_unmapped_count" in data["stage_breakdown"]
    assert data["stage_breakdown"]["_unmapped_count"] == 1
    unmapped_items = data["stage_breakdown"]["_unmapped_records"]
    assert any(u["application_no"] == "AICTE-TEST-UNKNOWN-99" for u in unmapped_items)
