import pytest
from datetime import datetime, date, timedelta, timezone
from fastapi.testclient import TestClient

from backend.seed.seed_data import seed_database
from backend.app.models.institution import Institution
from backend.app.models.application import Application
from backend.app.models.alert import Alert
from backend.app.models.audit import AuditEvent
from backend.app.services.audit_service import audit_service


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    return res.json()["access_token"]


def test_mandatory_p0_end_to_end_gate(client: TestClient, db_session):
    """
    MANDATORY P0 END-TO-END GATE VERIFICATION:
    1. An Institution Administrator submits a fictional application.
    2. An authorized officer sees it in the correctly scoped queue and performs a permitted workflow action.
    3. The application has a linked compliance obligation with a configurable demonstration deadline.
    4. The backend deadline evaluator creates the appropriate alert exactly once (idempotent).
    5. The case timeline and audit history reflect the persisted database state with valid cryptographic hash chain.
    6. A user with the wrong institution or region scope is denied access by the backend (HTTP 403).
    7. All automated checks pass against persisted state.
    """
    seed_database(db_session, generate_alerts=False)

    inst1_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    inst1 = db_session.query(Institution).filter(Institution.aicte_id == "1-100234501").first()

    # Step 1: Institution Administrator submits a fictional application
    create_res = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {inst1_token}"},
        json={
            "application_type": "New Technical Campus Approval (Route A)",
            "route": "ROUTE_A",
            "academic_year": "2026-2027"
        }
    )
    assert create_res.status_code == 201
    app_data = create_res.json()
    app_id = app_data["id"]
    app_no = app_data["application_no"]
    assert app_data["status"] == "DRAFT"

    # Submit application
    submit_res = client.post(
        f"/api/applications/{app_id}/submit",
        headers={"Authorization": f"Bearer {inst1_token}"}
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "SUBMITTED"

    # Step 2: Authorized Regional Officer sees it in regional queue and performs workflow transition
    ro_north_token = get_token_for(client, "ro_north@aicte.gov.in")
    ro_queue_res = client.get("/api/applications", headers={"Authorization": f"Bearer {ro_north_token}"})
    assert ro_queue_res.status_code == 200
    ro_apps = ro_queue_res.json()
    assert any(a["id"] == app_id for a in ro_apps)

    # RO transitions to UNDER_SCRUTINY
    trans_res = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_north_token}"},
        json={
            "action": "UNDER_SCRUTINY",
            "comments": "Initiated scrutiny of physical infrastructure and land deed documents."
        }
    )
    assert trans_res.status_code == 200
    assert trans_res.json()["status"] == "UNDER_SCRUTINY"

    # Step 3: Application has a linked compliance obligation with configurable deadline
    reviewer_token = get_token_for(client, "comp_review@aicte.gov.in")
    ob_res = client.post(
        "/api/compliance/obligations",
        headers={"Authorization": f"Bearer {reviewer_token}"},
        json={
            "institution_id": inst1.id,
            "application_id": app_id,
            "category": "FIRE_SAFETY",
            "title": "Municipal Fire Safety Clearance NOC",
            "description": "Condition Precedent: Submit valid municipal fire safety certificate.",
            "due_date": (date.today() + timedelta(days=5)).isoformat(),
            "condition_source": "APH 2026 Chapter I Standard Norms"
        }
    )
    assert ob_res.status_code == 201
    ob_id = ob_res.json()["id"]

    # Step 4: Backend deadline evaluator creates appropriate alert exactly once (idempotent)
    eval_res_1 = client.post(
        "/api/alerts/evaluate",
        headers={"Authorization": f"Bearer {ro_north_token}"}
    )
    assert eval_res_1.status_code == 200
    eval_data_1 = eval_res_1.json()
    assert eval_data_1["new_alerts_created"] > 0

    # Repeat evaluation - must create exactly zero duplicates
    eval_res_2 = client.post(
        "/api/alerts/evaluate",
        headers={"Authorization": f"Bearer {ro_north_token}"}
    )
    assert eval_res_2.status_code == 200
    eval_data_2 = eval_res_2.json()
    assert eval_data_2["new_alerts_created"] == 0
    assert eval_data_2["duplicate_alerts_skipped"] == eval_data_1["new_alerts_created"]

    # Step 5: Timeline and audit history reflect persisted database state and hash chain is intact
    app_details_res = client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {ro_north_token}"})
    assert app_details_res.status_code == 200
    app_details = app_details_res.json()
    assert len(app_details["history"]) >= 2  # Submission + Transition to SCRUTINY

    # Verify cryptographic hash chain on audit trail
    is_valid, count, broken_seq, msg = audit_service.verify_chain(db_session)
    assert is_valid is True
    assert count >= 3
    assert broken_seq is None

    # Step 6: User with wrong institution or Region scope is denied access (HTTP 403)
    # Institution 2 admin tries to view Institution 1 application
    inst2_token = get_token_for(client, "inst_admin2@fictional-poly.org")
    denied_view = client.get(f"/api/applications/{app_id}", headers={"Authorization": f"Bearer {inst2_token}"})
    assert denied_view.status_code == 403
    assert "Security violation" in denied_view.json()["detail"]

    # Regional Officer West tries to transition North application
    ro_west_token = get_token_for(client, "ro_west@aicte.gov.in")
    denied_trans = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {ro_west_token}"},
        json={
            "action": "SCHEDULE_EVC",
            "comments": "Illegitimate cross-region action attempt"
        }
    )
    assert denied_trans.status_code == 403
    assert "Security violation" in denied_trans.json()["detail"]

    # Step 7: Completed successfully with verified database persistence
    print(f"Mandatory P0 Gate successfully verified for Application {app_no} (ID: {app_id})!")
