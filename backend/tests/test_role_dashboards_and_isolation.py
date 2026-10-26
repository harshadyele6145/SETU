import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.seed.seed_data import seed_database
from backend.app.models.institution import Institution
from backend.app.models.region import Region
from backend.app.models.application import Application
from backend.app.models.user import User
from backend.app.models.evc import EVCVisit, EVCExpert
from backend.app.core.security import get_password_hash, create_access_token


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    return res.json()["access_token"]


def test_institution_admin_dashboard_isolation(client: TestClient, db_session: Session):
    """
    Verifies that INST_ADMIN receives only their own institution's data,
    has zero regional workload leakage, and role_view contains action-oriented queues.
    """
    seed_database(db_session, generate_alerts=True)

    token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    inst = db_session.query(Institution).filter(Institution.aicte_id == "1-100234501").first()

    res = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    # 1. Total isolation from regional workload
    assert data["regional_workload"] == []

    # 2. Scoped summary
    own_apps_count = db_session.query(Application).filter(Application.institution_id == inst.id).count()
    assert data["summary"]["total_applications"] == own_apps_count

    # 3. Role-specific action queues
    role_view = data["role_view"]
    assert role_view["role"] == "INST_ADMIN"
    assert "deficiency_notices" in role_view
    assert "pending_compliance" in role_view
    assert "document_reminders" in role_view
    assert "my_applications" in role_view

    # Verify all applications in my_applications belong to this institution
    for a in role_view["my_applications"]:
        db_app = db_session.get(Application, a["id"])
        assert db_app.institution_id == inst.id

    # 4. Applications endpoint isolation
    apps_res = client.get("/api/applications", headers={"Authorization": f"Bearer {token}"})
    assert apps_res.status_code == 200
    apps = apps_res.json()
    assert len(apps) == own_apps_count
    for a in apps:
        assert a["institution_name"] == inst.name

    # 5. Pendency report scoping
    rep_res = client.get("/api/reports/pendency", headers={"Authorization": f"Bearer {token}"})
    assert rep_res.status_code == 200
    rep_apps = rep_res.json()
    for ra in rep_apps:
        assert ra["institution_name"] == inst.name


def test_ro_officer_regional_dashboard_and_isolation(client: TestClient, db_session: Session):
    """
    Verifies that RO_OFFICER receives only their assigned region's workload,
    their scrutiny queue, and cannot access or modify applications outside their region.
    """
    seed_database(db_session, generate_alerts=True)

    token = get_token_for(client, "ro_north@aicte.gov.in")
    north_reg = db_session.query(Region).filter(Region.code == "RO_NORTH").first()
    west_reg = db_session.query(Region).filter(Region.code == "RO_WEST").first()

    res = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    # 1. Regional workload contains ONLY RO_NORTH
    assert len(data["regional_workload"]) == 1
    assert data["regional_workload"][0]["region_code"] == "RO_NORTH"

    # 2. Scrutiny queue presence
    role_view = data["role_view"]
    assert "scrutiny_queue" in role_view
    assert "deficiency_returns" in role_view
    assert "urgent_deadlines" in role_view

    # 3. Application list strictly scoped to North
    apps_res = client.get("/api/applications", headers={"Authorization": f"Bearer {token}"})
    assert apps_res.status_code == 200
    apps = apps_res.json()
    assert len(apps) > 0
    for a in apps:
        assert a["region_name"] == north_reg.name

    # 4. Cross-region schedule rejection
    west_app = db_session.query(Application).filter(Application.region_id == west_reg.id).first()
    schedule_res = client.post(
        "/api/evc/visits",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "application_id": west_app.id,
            "proposed_date": "2026-11-20"
        }
    )
    assert schedule_res.status_code == 403


def test_bureau_officer_and_competent_authority_cross_regional_dashboard(client: TestClient, db_session: Session):
    """
    Verifies that Bureau Officers and Competent Authorities have authorized cross-regional visibility.
    """
    seed_database(db_session, generate_alerts=True)
    
    # 1. Bureau Officer
    bo_token = get_token_for(client, "bo_officer@aicte.gov.in")
    bo_res = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {bo_token}"})
    assert bo_res.status_code == 200
    bo_data = bo_res.json()
    assert len(bo_data["regional_workload"]) == 5
    assert "national_summary" in bo_data["role_view"]

    # 2. Competent Authority
    ca_token = get_token_for(client, "comp_auth@aicte.gov.in")
    ca_res = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {ca_token}"})
    assert ca_res.status_code == 200
    ca_data = ca_res.json()
    assert len(ca_data["regional_workload"]) == 5
    assert "awaiting_statutory_decision" in ca_data["role_view"]


def test_committee_member_assigned_scope_isolation(client: TestClient, db_session: Session):
    """
    Verifies that Committee Members see NO regional workload, and can only see
    applications and visits where they are assigned as inspection experts.
    """
    seed_database(db_session, generate_alerts=True)

    token = get_token_for(client, "comm_member@aicte.gov.in")

    res = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    # Zero regional workload exposure
    assert data["regional_workload"] == []
    assert "assigned_inspections" in data["role_view"]

    # Applications list only contains assigned visits
    apps_res = client.get("/api/applications", headers={"Authorization": f"Bearer {token}"})
    assert apps_res.status_code == 200
    assigned_apps = apps_res.json()

    # For each returned application, verify an expert assignment exists with comm_member email
    for a in assigned_apps:
        is_assigned = (
            db_session.query(EVCVisit)
            .join(EVCExpert)
            .filter(
                EVCVisit.application_id == a["id"],
                EVCExpert.contact_email == "comm_member@aicte.gov.in"
            )
            .first()
        ) is not None
        assert is_assigned is True


def test_missing_scope_safety(client: TestClient, db_session: Session):
    """
    Security Invariant: If a user has a role requiring an institution_id or region_id,
    but that attribute is NULL/missing, the backend MUST NEVER fall back to unrestricted data.
    It must return 0 records and empty lists.
    """
    seed_database(db_session)

    # 1. Unassigned Institution Admin
    unassigned_inst_user = User(
        email="unassigned_inst@test.edu",
        hashed_password=get_password_hash("DemoPass@2026"),
        full_name="Unassigned Inst User",
        role="INST_ADMIN",
        institution_id=None,
        region_id=None,
        is_active=True
    )
    db_session.add(unassigned_inst_user)

    # 2. Unassigned Regional Officer
    unassigned_ro_user = User(
        email="unassigned_ro@aicte.gov.in",
        hashed_password=get_password_hash("DemoPass@2026"),
        full_name="Unassigned RO Officer",
        role="RO_OFFICER",
        institution_id=None,
        region_id=None,
        is_active=True
    )
    db_session.add(unassigned_ro_user)
    db_session.commit()

    token_inst = create_access_token({"sub": unassigned_inst_user.id, "email": unassigned_inst_user.email, "role": "INST_ADMIN"})
    token_ro = create_access_token({"sub": unassigned_ro_user.id, "email": unassigned_ro_user.email, "role": "RO_OFFICER"})

    # Check unassigned inst user: 0 applications, 0 workload
    stats_inst = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {token_inst}"}).json()
    assert stats_inst["summary"]["total_applications"] == 0
    assert stats_inst["regional_workload"] == []

    apps_inst = client.get("/api/applications", headers={"Authorization": f"Bearer {token_inst}"}).json()
    assert apps_inst == []

    # Check unassigned RO user: 0 applications, 0 workload
    stats_ro = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {token_ro}"}).json()
    assert stats_ro["summary"]["total_applications"] == 0
    assert stats_ro["regional_workload"] == []

    apps_ro = client.get("/api/applications", headers={"Authorization": f"Bearer {token_ro}"}).json()
    assert apps_ro == []


def test_dashboard_counts_match_scoped_list_endpoints(client: TestClient, db_session: Session):
    """
    Verifies that dashboard KPI summary counts exactly match the record count returned
    by scoped entity endpoints for both institutional and regional roles.
    """
    seed_database(db_session, generate_alerts=True)

    # Institutional Admin
    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    inst_stats = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {inst_token}"}).json()
    inst_apps = client.get("/api/applications", headers={"Authorization": f"Bearer {inst_token}"}).json()
    inst_obs = client.get("/api/compliance/obligations", headers={"Authorization": f"Bearer {inst_token}"}).json()
    inst_docs = client.get("/api/documents", headers={"Authorization": f"Bearer {inst_token}"}).json()

    assert inst_stats["summary"]["total_applications"] == len(inst_apps)
    assert inst_stats["compliance_health"]["total"] == len(inst_obs)
    assert inst_stats["document_health"]["total"] == len(inst_docs)

    # Regional Officer
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")
    ro_stats = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {ro_token}"}).json()
    ro_apps = client.get("/api/applications", headers={"Authorization": f"Bearer {ro_token}"}).json()
    ro_obs = client.get("/api/compliance/obligations", headers={"Authorization": f"Bearer {ro_token}"}).json()
    ro_docs = client.get("/api/documents", headers={"Authorization": f"Bearer {ro_token}"}).json()

    assert ro_stats["summary"]["total_applications"] == len(ro_apps)
    assert ro_stats["compliance_health"]["total"] == len(ro_obs)
    assert ro_stats["document_health"]["total"] == len(ro_docs)

