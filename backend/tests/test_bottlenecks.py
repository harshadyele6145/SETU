from fastapi.testclient import TestClient

from backend.seed.seed_data import seed_database
from backend.app.models.institution import Institution


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    return res.json()["access_token"]


def test_bottleneck_cockpit_categorization(client: TestClient, db_session):
    seed_database(db_session, generate_alerts=True)

    bo_token = get_token_for(client, "bo_officer@aicte.gov.in")

    res = client.get("/api/bottlenecks/exceptions", headers={"Authorization": f"Bearer {bo_token}"})
    assert res.status_code == 200
    data = res.json()

    assert "total_exceptions" in data
    assert "waiting_on_institution" in data
    assert "waiting_on_aicte" in data
    assert data["total_exceptions"] == data["waiting_on_institution"] + data["waiting_on_aicte"]
    assert len(data["items"]) == data["total_exceptions"]

    if data["items"]:
        first = data["items"][0]
        assert first["holding_side"] in ["WAITING_ON_INSTITUTION", "WAITING_ON_AICTE"]
        assert "responsible_party" in first
        assert "blocker_reason" in first
        assert "next_permissible_action" in first


def test_compliance_dependency_graph(client: TestClient, db_session):
    seed_database(db_session, generate_alerts=False)

    ro_token = get_token_for(client, "ro_north@aicte.gov.in")

    res = client.get("/api/bottlenecks/dependencies", headers={"Authorization": f"Bearer {ro_token}"})
    assert res.status_code == 200
    graph = res.json()

    assert "nodes" in graph
    assert "links" in graph
    assert len(graph["nodes"]) > 0
    assert len(graph["links"]) > 0

    node_types = {n["type"] for n in graph["nodes"]}
    assert "INSTITUTION" in node_types
    assert "APPLICATION" in node_types
