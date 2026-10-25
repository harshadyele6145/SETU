from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "platform" in data
    assert "version" in data
    assert data["health_check"] == "/health"


def test_health_endpoints(client: TestClient):
    for path in ["/health", "/ready", "/api/health"]:
        response = client.get(path)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert data["database_connected"] is True

