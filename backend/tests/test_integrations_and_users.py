from fastapi.testclient import TestClient
from backend.seed.seed_data import seed_database


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    return res.json()["access_token"]


def test_integration_monitor_adapter_and_failure_toggle(client: TestClient, db_session):
    seed_database(db_session)
    ca_token = get_token_for(client, "comp_auth@aicte.gov.in")
    headers = {"Authorization": f"Bearer {ca_token}"}

    # 1. Check initial status
    status_res = client.get("/api/integrations/status", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "health" in status_data
    assert "MockPortalAdapter" in status_data["health"]["adapter_name"]

    # 2. Test successful push decision
    push_res = client.post(
        "/api/integrations/test-push",
        headers=headers,
        json={
            "application_no": "AICTE/DEMO/2026/099",
            "decision": "APPROVED",
            "comments": "Automated verification test"
        }
    )
    assert push_res.status_code == 200
    push_data = push_res.json()
    assert push_data["success"] is True
    assert push_data["status_code"] == 200
    assert "AICTE-SYNC-" in push_data["external_reference_id"]

    # 3. Toggle failure mode to True
    toggle_res = client.post(
        "/api/integrations/toggle-failure",
        headers=headers,
        json={"simulate_failure": True}
    )
    assert toggle_res.status_code == 200
    assert toggle_res.json()["simulate_failure"] is True

    # 4. Push decision should now return simulated gateway error
    failed_push = client.post(
        "/api/integrations/test-push",
        headers=headers,
        json={
            "application_no": "AICTE/DEMO/2026/099",
            "decision": "APPROVED",
            "comments": "Failure test"
        }
    )
    assert failed_push.status_code == 200
    failed_data = failed_push.json()
    assert failed_data["success"] is False
    assert failed_data["status_code"] == 504
    assert "Simulated Gateway Timeout" in failed_data["message"]

    # 5. Fetch profile should return 503
    failed_fetch = client.get("/api/integrations/fetch-institution/1-3324567891", headers=headers)
    assert failed_fetch.status_code == 503

    # 6. Toggle failure back to False
    toggle_back = client.post(
        "/api/integrations/toggle-failure",
        headers=headers,
        json={"simulate_failure": False}
    )
    assert toggle_back.status_code == 200

    # 7. Fetch profile now succeeds
    succ_fetch = client.get("/api/integrations/fetch-institution/1-3324567891", headers=headers)
    assert succ_fetch.status_code == 200
    assert succ_fetch.json()["aicte_id"] == "1-3324567891"

    # 8. Prerequisites check
    prereq_res = client.get("/api/integrations/prerequisites", headers=headers)
    assert prereq_res.status_code == 200
    assert len(prereq_res.json()["prerequisites"]) >= 5


def test_users_api_scoped_listing_and_roles(client: TestClient, db_session):
    seed_database(db_session)

    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")
    ca_token = get_token_for(client, "comp_auth@aicte.gov.in")

    # 1. Institution Admin only sees own institution users
    inst_res = client.get("/api/users", headers={"Authorization": f"Bearer {inst_token}"})
    assert inst_res.status_code == 200
    inst_users = inst_res.json()
    assert len(inst_users) >= 1
    for u in inst_users:
        assert u["role"] == "INST_ADMIN"

    # 2. RO Officer sees users in their region
    ro_res = client.get("/api/users", headers={"Authorization": f"Bearer {ro_token}"})
    assert ro_res.status_code == 200
    ro_users = ro_res.json()
    # RO North should see users affiliated with Northern region or northern institutes
    assert len(ro_users) >= 1

    # 3. Competent Authority sees all users
    ca_res = client.get("/api/users", headers={"Authorization": f"Bearer {ca_token}"})
    assert ca_res.status_code == 200
    ca_users = ca_res.json()
    # Seed data has at least 10 users across 8 roles
    assert len(ca_users) >= 10
    comp_auths = [u for u in ca_users if u["role"] == "COMP_AUTH"]
    assert len(comp_auths) >= 1
    assert comp_auths[0]["statutory_authority"] is True

    # 4. Check 8 role definitions
    roles_res = client.get("/api/users/roles", headers={"Authorization": f"Bearer {ca_token}"})
    assert roles_res.status_code == 200
    roles = roles_res.json()
    assert len(roles) == 8
    role_keys = {r["role_key"] for r in roles}
    expected_keys = {
        "INST_ADMIN", "RO_OFFICER", "REGIONAL_DIR", "BUREAU_OFFICER",
        "EVC_COORD", "COMMITTEE_MBR", "COMP_REV", "COMP_AUTH"
    }
    assert role_keys == expected_keys
