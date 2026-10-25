from fastapi.testclient import TestClient
from backend.seed.seed_data import seed_database
from backend.app.models.audit import AuditEvent
from backend.app.services.audit_service import audit_service


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    return res.json()["access_token"]


def test_audit_hash_chain_validity_after_actions(client: TestClient, db_session):
    seed_database(db_session)

    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")

    # Perform multiple auditable actions
    app_res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"academic_year": "2026-2027", "application_type": "EoA", "route": "ROUTE_A"}
    )
    app_id = app_res.json()["id"]

    client.post(f"/api/applications/{app_id}/submit", headers={"Authorization": f"Bearer {inst_token}"})
    client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"action": "UNDER_SCRUTINY", "comments": "Commencing scrutiny."}
    )

    # Verify chain via service directly
    is_valid, total_checked, broken_seq, msg = audit_service.verify_chain(db_session)
    assert is_valid is True
    assert total_checked > 0
    assert broken_seq is None
    assert "intact" in msg

    # Verify chain via API endpoint
    api_verify = client.get("/api/audit/verify-chain", headers={"Authorization": f"Bearer {ro_token}"})
    assert api_verify.status_code == 200
    res_data = api_verify.json()
    assert res_data["is_valid"] is True
    assert res_data["total_events_checked"] == total_checked


def test_audit_hash_chain_tamper_detection(client: TestClient, db_session):
    seed_database(db_session)

    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    app_res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"academic_year": "2026-2027", "application_type": "EoA", "route": "ROUTE_A"}
    )

    # Retrieve an event and maliciously tamper with its stored payload directly in database
    target_event = db_session.query(AuditEvent).filter(AuditEvent.sequence_no > 1).first()
    assert target_event is not None
    tampered_seq = target_event.sequence_no

    # Malicious direct modification
    target_event.action = "MALICIOUSLY_ALTERED_ACTION"
    db_session.flush()

    # Verify that the cryptographic hash chain catches the modification!
    is_valid, total_checked, broken_seq, msg = audit_service.verify_chain(db_session)
    assert is_valid is False
    assert broken_seq == tampered_seq
    assert "tamper detected" in msg.lower()

