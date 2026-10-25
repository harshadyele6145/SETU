from fastapi.testclient import TestClient

from backend.seed.seed_data import seed_database
from backend.app.models.institution import Institution
from backend.app.models.application import Application


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    return res.json()["access_token"]


def test_explainable_attention_engine_scoring_and_explanation(client: TestClient, db_session):
    seed_database(db_session, generate_alerts=True)

    ro_token = get_token_for(client, "ro_north@aicte.gov.in")
    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")

    # 1. Fetch Attention Queue as Regional Officer
    res = client.get("/api/attention/queue", headers={"Authorization": f"Bearer {ro_token}"})
    assert res.status_code == 200
    queue = res.json()
    assert len(queue) > 0

    # Invariant: Queue is deterministically ordered by composite score descending
    scores = [item["composite_score"] for item in queue]
    assert scores == sorted(scores, reverse=True)

    # Check top priority item
    top_item = queue[0]
    assert "priority_level" in top_item
    assert top_item["priority_level"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    assert "responsible_role" in top_item
    assert "blocking_dependency" in top_item
    assert "recommended_action" in top_item
    assert "explanation" in top_item
    assert len(top_item["factors"]) > 0

    # Verify factor structure
    f1 = top_item["factors"][0]
    assert "factor_name" in f1
    assert "points_awarded" in f1
    assert "rationale" in f1

    # 2. Case structured summary
    app_id = top_item["application_id"]
    summary_res = client.get(
        f"/api/attention/applications/{app_id}/summary",
        headers={"Authorization": f"Bearer {ro_token}"}
    )
    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    q = summary_data["questions"]
    assert "q1_what_needs_attention" in q
    assert "q2_why_pending" in q
    assert "q3_who_responsible" in q
    assert "q4_what_happens_next" in q
    assert "q5_can_be_traced" in q


def test_attention_case_summary_scoping_enforced(client: TestClient, db_session):
    seed_database(db_session, generate_alerts=False)

    inst1_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    inst1 = db_session.query(Institution).filter(Institution.aicte_id == "1-100234501").first()

    # Find application of a DIFFERENT institution
    other_app = db_session.query(Application).filter(Application.institution_id != inst1.id).first()
    assert other_app is not None

    # Inst 1 attempts to access other institution's case summary -> HTTP 403 Forbidden
    res = client.get(
        f"/api/attention/applications/{other_app.id}/summary",
        headers={"Authorization": f"Bearer {inst1_token}"}
    )
    assert res.status_code == 403
