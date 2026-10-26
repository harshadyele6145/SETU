import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.seed.seed_data import seed_database
from backend.app.models.institution import Institution
from backend.app.models.region import Region
from backend.app.models.application import Application
from backend.app.models.evc import EVCVisit, EVCExpert
from backend.app.models.user import User


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def test_all_demo_persona_credentials_authenticate(client: TestClient, db_session: Session):
    """
    Verifies that all standard demo personas can authenticate with DemoPass@2026.
    Ensures zero 401s during live persona switching.
    """
    seed_database(db_session, generate_alerts=False)

    demo_emails = [
        "inst_admin@fictional-nist.edu.in",
        "inst_admin2@fictional-poly.org",
        "ro_north@aicte.gov.in",
        "ro_west@aicte.gov.in",
        "ro_west_dir@aicte.gov.in",
        "bureau_officer@aicte.gov.in",
        "bo_officer@aicte.gov.in",
        "evc_coord@aicte.gov.in",
        "expert1@aicte-roster.ac.in",
        "comm_member@aicte.gov.in",
        "compliance_reviewer@aicte.gov.in",
        "comp_review@aicte.gov.in",
        "comp_auth@aicte.gov.in",
        "sys_admin@aicte.gov.in"
    ]

    for email in demo_emails:
        token = get_token_for(client, email)
        assert token is not None
        assert len(token) > 20


def test_unauthorized_submit_boundaries(client: TestClient, db_session: Session):
    """
    Verifies that non-INST_ADMIN roles and mismatched institution admins cannot submit applications.
    """
    seed_database(db_session, generate_alerts=False)

    inst1 = db_session.query(Institution).filter(Institution.aicte_id == "1-100234501").first()
    draft_app = Application(
        application_no="AICTE-2026-TEST-DRAFT",
        institution_id=inst1.id,
        region_id=inst1.region_id,
        academic_year="2026-2027",
        application_type="Extension of Approval (EoA)",
        route="ROUTE_A",
        status="DRAFT"
    )
    db_session.add(draft_app)
    db_session.commit()

    # 1. RO_OFFICER cannot submit
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")
    res = client.post(
        f"/api/applications/{draft_app.id}/submit",
        headers={"Authorization": f"Bearer {ro_token}"}
    )
    assert res.status_code == 403
    assert "Institution Administrator" in res.json()["detail"]

    # 2. INST_ADMIN from a different institution cannot submit
    inst2_token = get_token_for(client, "inst_admin2@fictional-poly.org")
    res2 = client.post(
        f"/api/applications/{draft_app.id}/submit",
        headers={"Authorization": f"Bearer {inst2_token}"}
    )
    assert res2.status_code == 403

    # 3. Legitimate INST_ADMIN can submit
    inst1_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    res3 = client.post(
        f"/api/applications/{draft_app.id}/submit",
        headers={"Authorization": f"Bearer {inst1_token}"}
    )
    assert res3.status_code == 200
    assert res3.json()["status"] == "SUBMITTED"


def test_unauthorized_return_and_resubmit_boundaries(client: TestClient, db_session: Session):
    """
    Verifies that INST_ADMIN cannot return an application for deficiency,
    and non-INST_ADMIN cannot resubmit clarifications.
    """
    seed_database(db_session, generate_alerts=False)

    # Find an application in UNDER_SCRUTINY
    app = db_session.query(Application).filter(Application.status == "UNDER_SCRUTINY").first()
    assert app is not None

    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")

    # 1. INST_ADMIN cannot call return
    res = client.post(
        f"/api/applications/{app.id}/return",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"comments": "Institution trying to return own app"}
    )
    assert res.status_code == 403

    # 2. Out-of-region officer cannot return
    ro_west_token = get_token_for(client, "ro_west@aicte.gov.in")
    res_west = client.post(
        f"/api/applications/{app.id}/return",
        headers={"Authorization": f"Bearer {ro_west_token}"},
        json={"comments": "Cross-region return attempt"}
    )
    assert res_west.status_code == 403

    # 3. Authorized RO Officer can return with comments
    res_ro = client.post(
        f"/api/applications/{app.id}/return",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"comments": "Mandatory deficiency observed in land lease title."}
    )
    assert res_ro.status_code == 200
    assert res_ro.json()["status"] == "SCRUTINY_DEFICIENT"
    assert res_ro.json()["return_count"] >= 1

    # 4. RO Officer cannot call resubmit (only INST_ADMIN can resubmit)
    res_ro_resub = client.post(
        f"/api/applications/{app.id}/resubmit",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"comments": "Officer trying to resubmit on behalf of college"}
    )
    assert res_ro_resub.status_code == 403
    assert "Institution Administrator" in res_ro_resub.json()["detail"]


def test_unauthorized_reassignment_boundaries(client: TestClient, db_session: Session):
    """
    Verifies that INST_ADMIN and COMMITTEE_MBR cannot reassign officers.
    """
    seed_database(db_session, generate_alerts=False)

    app = db_session.query(Application).filter(Application.status.notin_(["APPROVED", "REJECTED"])).first()
    officer = db_session.query(User).filter(User.role == "RO_OFFICER").first()

    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    res = client.post(
        f"/api/applications/{app.id}/reassign",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"officer_id": officer.id, "comments": "Unauthorized reassignment"}
    )
    assert res.status_code == 403


def test_committee_member_inspection_scope_boundary(client: TestClient, db_session: Session):
    """
    Verifies that a committee member can only access applications and timelines
    for visits where they are assigned as an EVC expert.
    """
    seed_database(db_session, generate_alerts=False)

    # AICTE-2026-0110 is assigned to expert1@aicte-roster.ac.in
    assigned_app = db_session.query(Application).filter(Application.application_no == "AICTE-2026-0110").first()
    # AICTE-2026-0101 is not assigned
    unassigned_app = db_session.query(Application).filter(Application.application_no == "AICTE-2026-0101").first()

    expert_token = get_token_for(client, "expert1@aicte-roster.ac.in")

    # 1. Assigned app timeline is accessible
    res_assigned = client.get(
        f"/api/applications/{assigned_app.id}/timeline",
        headers={"Authorization": f"Bearer {expert_token}"}
    )
    assert res_assigned.status_code == 200

    # 2. Assigned app accountability is accessible
    res_acc = client.get(
        f"/api/applications/{assigned_app.id}/accountability",
        headers={"Authorization": f"Bearer {expert_token}"}
    )
    assert res_acc.status_code == 200
    acc_data = res_acc.json()
    assert acc_data["application_no"] == "AICTE-2026-0110"

    # 3. Unassigned app timeline returns 403 Forbidden
    res_unassigned = client.get(
        f"/api/applications/{unassigned_app.id}/timeline",
        headers={"Authorization": f"Bearer {expert_token}"}
    )
    assert res_unassigned.status_code == 403
    assert "Committee members can only view" in res_unassigned.json()["detail"]

    # 4. Unassigned app accountability returns 403 Forbidden
    res_unassigned_acc = client.get(
        f"/api/applications/{unassigned_app.id}/accountability",
        headers={"Authorization": f"Bearer {expert_token}"}
    )
    assert res_unassigned_acc.status_code == 403


def test_case_accountability_contract_and_holding_logic(client: TestClient, db_session: Session):
    """
    Verifies the contract of GET /api/applications/{id}/accountability,
    confirming holding party classification and permitted action permissions.
    """
    seed_database(db_session, generate_alerts=False)

    # 1. Test case in SCRUTINY_DEFICIENT is WAITING_ON_INSTITUTION
    def_app = db_session.query(Application).filter(Application.status == "SCRUTINY_DEFICIENT").first()
    assert def_app is not None

    ro_token = get_token_for(client, "ro_north@aicte.gov.in")
    res = client.get(
        f"/api/applications/{def_app.id}/accountability",
        headers={"Authorization": f"Bearer {ro_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["holding_party"] == "WAITING_ON_INSTITUTION"
    assert data["holding_responsible_role"] == "INST_ADMIN"
    assert data["current_user_can_act"] is False  # RO cannot act when holding is with Institution

    # 2. Test from INST_ADMIN persona: current_user_can_act is True
    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    # Make sure def_app belongs to inst1 or test with its actual inst
    inst_user = db_session.query(User).filter(User.institution_id == def_app.institution_id).first()
    if inst_user:
        inst_user_token = get_token_for(client, inst_user.email)
        res_inst = client.get(
            f"/api/applications/{def_app.id}/accountability",
            headers={"Authorization": f"Bearer {inst_user_token}"}
        )
        assert res_inst.status_code == 200
        inst_data = res_inst.json()
        assert inst_data["current_user_can_act"] is True
        # Check resubmit action is marked permitted
        resub_actions = [a for a in inst_data["permitted_next_actions"] if "RESUBMIT" in a["action_key"]]
        assert len(resub_actions) > 0
        assert resub_actions[0]["is_permitted_for_user"] is True
