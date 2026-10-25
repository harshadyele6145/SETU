from fastapi.testclient import TestClient

from backend.seed.seed_data import seed_database
from backend.app.models.institution import Institution
from backend.app.models.application import Application


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    return res.json()["access_token"]


def test_dashboard_metrics_dynamic_calculation(client: TestClient, db_session):
    seed_database(db_session, generate_alerts=True)

    bo_token = get_token_for(client, "bo_officer@aicte.gov.in")
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")
    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")

    # 1. National level metrics (BO Officer)
    bo_res = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {bo_token}"})
    assert bo_res.status_code == 200
    bo_data = bo_res.json()
    total_db_apps = db_session.query(Application).count()
    assert bo_data["summary"]["total_applications"] == total_db_apps
    assert len(bo_data["regional_workload"]) == 5  # 5 regions
    assert sum(r["count"] for r in bo_data["route_distribution"]) == total_db_apps

    # 2. Regional level metrics (RO North)
    ro_res = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {ro_token}"})
    assert ro_res.status_code == 200
    ro_data = ro_res.json()
    assert ro_data["summary"]["total_applications"] < total_db_apps
    assert ro_data["summary"]["total_applications"] > 0

    # 3. Institutional level metrics (Institution Admin)
    inst_res = client.get("/api/dashboard/stats", headers={"Authorization": f"Bearer {inst_token}"})
    assert inst_res.status_code == 200
    inst_data = inst_res.json()
    assert inst_data["summary"]["total_applications"] >= 1
    assert inst_data["summary"]["total_applications"] < ro_data["summary"]["total_applications"]


def test_pendency_reports_and_csv_export(client: TestClient, db_session):
    seed_database(db_session, generate_alerts=False)

    ro_token = get_token_for(client, "ro_north@aicte.gov.in")

    # Query pendency report JSON
    rep_res = client.get("/api/reports/pendency", headers={"Authorization": f"Bearer {ro_token}"})
    assert rep_res.status_code == 200
    rows = rep_res.json()
    assert len(rows) > 0
    first_row = rows[0]
    assert "application_no" in first_row
    assert "stage_age_days" in first_row
    assert "holding_party" in first_row

    # Export CSV
    csv_res = client.get("/api/reports/export", headers={"Authorization": f"Bearer {ro_token}"})
    assert csv_res.status_code == 200
    assert csv_res.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=setu_pendency_report.csv" in csv_res.headers["content-disposition"]
    csv_text = csv_res.text
    assert "Application No,Institution Name,Region" in csv_text
    assert first_row["application_no"] in csv_text
