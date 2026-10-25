import io
from datetime import date, timedelta
from fastapi.testclient import TestClient

from backend.seed.seed_data import seed_database
from backend.app.models.institution import Institution
from backend.app.models.application import Application
from backend.app.models.evc import EVCVisit, EVCExpert


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    return res.json()["access_token"]


def test_evc_scheduling_and_mandatory_reschedule_reason(client: TestClient, db_session):
    seed_database(db_session, generate_alerts=False)

    ro_north_token = get_token_for(client, "ro_north@aicte.gov.in")
    inst1 = db_session.query(Institution).filter(Institution.aicte_id == "1-100234501").first()
    app = db_session.query(Application).filter(Application.institution_id == inst1.id).first()

    # 1. Schedule EVC Visit
    visit_date = (date.today() + timedelta(days=10)).isoformat()
    sched_res = client.post(
        "/api/evc/visits",
        headers={"Authorization": f"Bearer {ro_north_token}"},
        json={
            "application_id": app.id,
            "proposed_date": visit_date
        }
    )
    assert sched_res.status_code == 201
    visit_data = sched_res.json()
    visit_id = visit_data["id"]
    assert visit_data["status"] == "SCHEDULED"
    assert visit_data["confirmed_date"] == visit_date

    # 2. Attempt to reschedule WITHOUT a delay reason -> Fails with HTTP 400
    resched_fail = client.post(
        f"/api/evc/visits/{visit_id}/reschedule",
        headers={"Authorization": f"Bearer {ro_north_token}"},
        json={
            "new_date": (date.today() + timedelta(days=15)).isoformat(),
            "delay_reason": "   "  # Empty / whitespace reason rejected
        }
    )
    assert resched_fail.status_code == 400
    assert "Mandatory justification" in resched_fail.json()["detail"]

    # 3. Reschedule with valid delay reason -> Succeeds
    new_date = (date.today() + timedelta(days=15)).isoformat()
    resched_ok = client.post(
        f"/api/evc/visits/{visit_id}/reschedule",
        headers={"Authorization": f"Bearer {ro_north_token}"},
        json={
            "new_date": new_date,
            "delay_reason": "Institution requested deferral due to university semester examinations."
        }
    )
    assert resched_ok.status_code == 200
    assert resched_ok.json()["confirmed_date"] == new_date
    assert "examinations" in resched_ok.json()["delay_reason"]

    # 4. Assign expert to visit roster
    expert_res = client.post(
        f"/api/evc/visits/{visit_id}/experts",
        headers={"Authorization": f"Bearer {ro_north_token}"},
        json={
            "expert_name": "Prof. D. K. Banerji",
            "designation": "Professor of Civil Engineering",
            "organization": "IIT Roorkee",
            "contact_email": "dkbanerji@iitr.ac.in"
        }
    )
    assert expert_res.status_code == 201
    assert expert_res.json()["expert_name"] == "Prof. D. K. Banerji"

    # 5. Submit EVC Inspection Report
    dummy_report = io.BytesIO(b"%PDF-1.4 Simulated EVC physical inspection findings report")
    report_res = client.post(
        f"/api/evc/visits/{visit_id}/report",
        headers={"Authorization": f"Bearer {ro_north_token}"},
        data={"report_summary": "Inspected all labs, library volumes, and physical barriers. Conforms to norms."},
        files={"file": ("evc_inspection_report.pdf", dummy_report, "application/pdf")}
    )
    assert report_res.status_code == 200
    assert report_res.json()["status"] == "REPORT_SUBMITTED"
    assert report_res.json()["completed_date"] is not None


def test_evc_cross_region_access_denied(client: TestClient, db_session):
    seed_database(db_session, generate_alerts=False)

    ro_west_token = get_token_for(client, "ro_west@aicte.gov.in")
    inst_north = db_session.query(Institution).filter(Institution.aicte_id == "1-100234501").first()
    app_north = db_session.query(Application).filter(Application.institution_id == inst_north.id).first()

    # RO West attempts to schedule EVC for Northern application -> HTTP 403 Forbidden
    sched_fail = client.post(
        "/api/evc/visits",
        headers={"Authorization": f"Bearer {ro_west_token}"},
        json={
            "application_id": app_north.id,
            "proposed_date": (date.today() + timedelta(days=10)).isoformat()
        }
    )
    assert sched_fail.status_code == 403
    assert "Security violation" in sched_fail.json()["detail"]
