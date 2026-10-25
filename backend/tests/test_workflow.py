from fastapi.testclient import TestClient
from backend.seed.seed_data import seed_database
from backend.app.models.application import Application


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    return res.json()["access_token"]


def test_workflow_route_a_complete_lifecycle(client: TestClient, db_session):
    seed_database(db_session)

    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")
    ca_token = get_token_for(client, "comp_auth@aicte.gov.in")

    # 1. Institution creates application
    create_res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "academic_year": "2026-2027",
            "application_type": "Extension of Approval (EoA)",
            "route": "ROUTE_A"
        }
    )
    assert create_res.status_code == 201
    app_data = create_res.json()
    app_id = app_data["id"]
    assert app_data["status"] == "DRAFT"

    # 2. Institution submits application
    submit_res = client.post(
        f"/api/applications/{app_id}/submit",
        headers={"Authorization": f"Bearer {inst_token}"}
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "SUBMITTED"

    # 3. RO moves application to UNDER_SCRUTINY
    scrutiny_res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"action": "UNDER_SCRUTINY", "comments": "Commencing scrutiny of uploaded compliance certificates."}
    )
    assert scrutiny_res.status_code == 200
    assert scrutiny_res.json()["status"] == "UNDER_SCRUTINY"

    # 4. RO clears scrutiny to SCRUTINY_RECOMMENDED
    rec_res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"action": "SCRUTINY_RECOMMENDED", "comments": "Scrutiny committee found all land and faculty proofs satisfactory."}
    )
    assert rec_res.status_code == 200
    assert rec_res.json()["status"] == "SCRUTINY_RECOMMENDED"

    # 5. RO moves to DECISION_PENDING
    dec_pending_res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"action": "DECISION_PENDING", "comments": "Forwarded to Competent Authority for statutory approval."}
    )
    assert dec_pending_res.status_code == 200
    assert dec_pending_res.json()["status"] == "DECISION_PENDING"

    # 6. Statutory Safeguard: Regional Officer CANNOT approve (403 Forbidden)
    ro_approve_attempt = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"action": "APPROVED", "comments": "Attempting unauthorized approval."}
    )
    assert ro_approve_attempt.status_code == 403
    assert "Competent Authority" in ro_approve_attempt.json()["detail"]

    # 7. Competent Authority issues statutory approval
    ca_approve_res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ca_token}"},
        json={"action": "APPROVED", "comments": "Final statutory approval accorded per APH norms."}
    )
    assert ca_approve_res.status_code == 200
    assert ca_approve_res.json()["status"] == "APPROVED"


def test_deficiency_return_and_clarification_resubmission(client: TestClient, db_session):
    seed_database(db_session)

    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")

    # Create and submit
    app_res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"academic_year": "2026-2027", "application_type": "EoA", "route": "ROUTE_A"}
    )
    app_id = app_res.json()["id"]
    client.post(f"/api/applications/{app_id}/submit", headers={"Authorization": f"Bearer {inst_token}"})
    client.post(f"/api/applications/{app_id}/transition", headers={"Authorization": f"Bearer {ro_token}"}, json={"action": "UNDER_SCRUTINY"})

    # Invariant INV-02: Empty return reason must fail with 400
    empty_return = client.post(
        f"/api/applications/{app_id}/return",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"comments": "   "}
    )
    assert empty_return.status_code == 400
    assert "Mandatory requirement" in empty_return.json()["detail"]

    # Valid return with non-empty deficiency reason
    valid_return = client.post(
        f"/api/applications/{app_id}/return",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"comments": "Structural stability certificate has expired. Upload renewal from certified civil authority."}
    )
    assert valid_return.status_code == 200
    assert valid_return.json()["status"] == "SCRUTINY_DEFICIENT"
    assert valid_return.json()["return_count"] == 1

    # Institution resubmits clarification
    resubmit = client.post(
        f"/api/applications/{app_id}/resubmit",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"comments": "Uploaded renewed Structural Stability Certificate valid until 2029."}
    )
    assert resubmit.status_code == 200
    assert resubmit.json()["status"] == "UNDER_SCRUTINY"
    assert resubmit.json()["return_count"] == 1


def test_forbidden_workflow_transitions(client: TestClient, db_session):
    seed_database(db_session)

    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")

    app_res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"academic_year": "2026-2027", "application_type": "EoA", "route": "ROUTE_A"}
    )
    app_id = app_res.json()["id"]

    # Cannot skip from DRAFT straight to UNDER_SCRUTINY
    invalid_skip = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"action": "UNDER_SCRUTINY"}
    )
    assert invalid_skip.status_code == 400
    assert "Invalid transition" in invalid_skip.json()["detail"]


def test_cross_region_modification_rejected(client: TestClient, db_session):
    seed_database(db_session)

    # Institution 1 is in Northern Region
    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    ro_west_token = get_token_for(client, "ro_west@aicte.gov.in")

    app_res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"academic_year": "2026-2027", "application_type": "EoA", "route": "ROUTE_A"}
    )
    app_id = app_res.json()["id"]
    client.post(f"/api/applications/{app_id}/submit", headers={"Authorization": f"Bearer {inst_token}"})

    # Regional Officer West attempts to transition Northern application
    cross_reg_attempt = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_west_token}"},
        json={"action": "UNDER_SCRUTINY"}
    )
    assert cross_reg_attempt.status_code == 403
    assert "Regional Officer cannot access or modify cases outside their designated Region" in cross_reg_attempt.json()["detail"]
