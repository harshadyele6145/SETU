import pytest
from datetime import datetime, date, timedelta, timezone
from fastapi.testclient import TestClient

from backend.seed.seed_data import seed_database
from backend.app.models.institution import Institution
from backend.app.models.application import Application
from backend.app.models.alert import Alert
from backend.app.models.notification import NotificationOutbox
from backend.app.services.alert_service import AlertService


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    return res.json()["access_token"]


def test_idempotent_alert_generation(client: TestClient, db_session):
    """
    Verifies that running deadline evaluation produces alerts, but repeated runs
    skip exact duplicates based on compound idempotency keys.
    """
    seed_database(db_session)
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")

    # First evaluation run
    res1 = client.post(
        "/api/alerts/evaluate",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"fail_notifications": False}
    )
    assert res1.status_code == 200
    data1 = res1.json()
    new_alerts_1 = data1["new_alerts_created"]
    assert new_alerts_1 > 0
    assert data1["duplicate_alerts_skipped"] == 0

    total_alerts_db_1 = db_session.query(Alert).count()
    assert total_alerts_db_1 == new_alerts_1

    # Second evaluation run immediately after
    res2 = client.post(
        "/api/alerts/evaluate",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"fail_notifications": False}
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["new_alerts_created"] == 0  # Zero duplicate alerts created
    assert data2["duplicate_alerts_skipped"] == new_alerts_1

    total_alerts_db_2 = db_session.query(Alert).count()
    assert total_alerts_db_2 == total_alerts_db_1  # Database state unchanged


def test_scoped_alert_visibility_and_cross_institution_protection(client: TestClient, db_session):
    """
    Verifies that Institution Administrator only sees and acknowledges alerts for their own institution.
    """
    seed_database(db_session)

    # Trigger alert generation as Bureau Officer
    bo_token = get_token_for(client, "bo_officer@aicte.gov.in")
    eval_res = client.post("/api/alerts/evaluate", headers={"Authorization": f"Bearer {bo_token}"})
    assert eval_res.status_code == 200

    inst1_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    inst1 = db_session.query(Institution).filter(Institution.aicte_id == "1-100234501").first()

    # Query alerts as inst1
    list_res = client.get("/api/alerts", headers={"Authorization": f"Bearer {inst1_token}"})
    assert list_res.status_code == 200
    inst1_alerts = list_res.json()
    assert len(inst1_alerts) > 0
    for a in inst1_alerts:
        assert a["institution_id"] == inst1.id

    # Find an alert belonging to a DIFFERENT institution
    other_alert = db_session.query(Alert).filter(
        Alert.institution_id.isnot(None),
        Alert.institution_id != inst1.id
    ).first()
    assert other_alert is not None

    # Institution 1 attempts to acknowledge other institution's alert -> Forbidden
    ack_forbidden = client.post(
        f"/api/alerts/{other_alert.id}/acknowledge",
        headers={"Authorization": f"Bearer {inst1_token}"}
    )
    assert ack_forbidden.status_code == 403
    assert "Access denied" in ack_forbidden.json()["detail"]

    # Institution 1 acknowledges their OWN alert -> Success
    my_alert = inst1_alerts[0]
    ack_success = client.post(
        f"/api/alerts/{my_alert['id']}/acknowledge",
        headers={"Authorization": f"Bearer {inst1_token}"}
    )
    assert ack_success.status_code == 200
    assert ack_success.json()["is_acknowledged"] is True
    assert ack_success.json()["acknowledged_by_name"] == "Dr. R. K. Verma (Inst Admin 1)"


def test_notification_outbox_retry_and_exhaustion(client: TestClient, db_session):
    """
    Verifies outbox failure simulation, retry tracking, exhaustion, and manual retry.
    """
    seed_database(db_session)
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")

    # Evaluate with fail_notifications = True (simulates transient SMTP timeout)
    res = client.post(
        "/api/alerts/evaluate",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"fail_notifications": True}
    )
    assert res.status_code == 200
    summary = res.json()["dispatch_summary"]
    assert summary["retrying"] > 0

    # View outbox notifications
    notif_res = client.get("/api/alerts/notifications", headers={"Authorization": f"Bearer {ro_token}"})
    assert notif_res.status_code == 200
    notifs = notif_res.json()
    assert len(notifs) > 0
    first_notif = notifs[0]
    assert first_notif["status"] in ["RETRYING", "PENDING"]
    assert first_notif["retry_count"] == 1

    # Simulate additional failed dispatches until max retries reached
    AlertService.dispatch_notifications(db_session, max_retries=3, fail_simulation=True)
    AlertService.dispatch_notifications(db_session, max_retries=3, fail_simulation=True)

    # Check that notification is now FAILED
    notif_obj = db_session.query(NotificationOutbox).filter(NotificationOutbox.id == first_notif["id"]).first()
    assert notif_obj.status == "FAILED"
    assert "exhausted" in notif_obj.last_error

    # Test manual retry endpoint
    retry_res = client.post(
        f"/api/alerts/notifications/{notif_obj.id}/retry",
        headers={"Authorization": f"Bearer {ro_token}"}
    )
    assert retry_res.status_code == 200
    retried_data = retry_res.json()
    assert retried_data["status"] == "SENT"
    assert retried_data["retry_count"] == 0
    assert retried_data["last_error"] is None


def test_downtime_recovery_catchup(client: TestClient, db_session):
    """
    Simulates downtime recovery where scheduler was offline, and a future evaluation run
    catches up by identifying newly breached deadlines.
    """
    seed_database(db_session)
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")

    # Normal evaluation run
    res1 = client.post("/api/alerts/evaluate", headers={"Authorization": f"Bearer {ro_token}"})
    initial_alerts = res1.json()["new_alerts_created"]

    # Now simulate time moving forward by 60 days (scheduler was offline during this time)
    future_date = (datetime.now(timezone.utc) + timedelta(days=60)).isoformat()

    res_catchup = client.post(
        "/api/alerts/evaluate",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"simulated_date": future_date}
    )
    assert res_catchup.status_code == 200
    catchup_data = res_catchup.json()
    
    # Catchup run must have detected new deadlines/breaches that occurred during the 60 days
    assert catchup_data["new_alerts_created"] > 0
    
    # Verify overdue alerts are generated with escalated severity
    overdue_alerts = db_session.query(Alert).filter(Alert.severity.in_(["HIGH", "CRITICAL"])).all()
    assert len(overdue_alerts) > 0
