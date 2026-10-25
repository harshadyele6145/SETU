from fastapi.testclient import TestClient
from backend.seed.seed_data import seed_database


def test_login_success(client: TestClient, db_session):
    # Seed data into test db
    seed_database(db_session)

    response = client.post(
        "/api/auth/login",
        json={"email": "ro_north@aicte.gov.in", "password": "DemoPass@2026"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "RO_OFFICER"
    assert data["email"] == "ro_north@aicte.gov.in"
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client: TestClient, db_session):
    seed_database(db_session)

    response = client.post(
        "/api/auth/login",
        json={"email": "ro_north@aicte.gov.in", "password": "WrongPassword123"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient, db_session):
    response = client.post(
        "/api/auth/login",
        json={"email": "ghost@aicte.gov.in", "password": "DemoPass@2026"}
    )
    assert response.status_code == 401


def test_get_current_user_profile(client: TestClient, db_session):
    seed_database(db_session)

    # Login
    login_res = client.post(
        "/api/auth/login",
        json={"email": "comp_auth@aicte.gov.in", "password": "DemoPass@2026"}
    )
    token = login_res.json()["access_token"]

    # Profile
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    user_info = res.json()
    assert user_info["role"] == "COMP_AUTH"
    assert user_info["email"] == "comp_auth@aicte.gov.in"


def test_unauthenticated_access_rejected(client: TestClient):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
