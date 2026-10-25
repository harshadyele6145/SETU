import io
from fastapi.testclient import TestClient
from backend.seed.seed_data import seed_database


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    return res.json()["access_token"]


def test_document_extraction_and_discrepancy_detection(client: TestClient, db_session):
    seed_database(db_session)
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")
    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")

    # 1. Fetch document list
    docs_res = client.get("/api/documents", headers={"Authorization": f"Bearer {ro_token}"})
    assert docs_res.status_code == 200
    docs = docs_res.json()
    assert len(docs) > 0
    test_doc = docs[0]

    # 2. Extract and analyze document
    extract_res = client.get(
        f"/api/documents/{test_doc['id']}/extract",
        headers={"Authorization": f"Bearer {ro_token}"}
    )
    assert extract_res.status_code == 200
    data = extract_res.json()
    assert data["extraction_status"] == "COMPLETED"
    assert "confidence_score" in data
    assert "confidence_level" in data
    assert data["human_verification_mandated"] is True
    assert "Invariant INV-01" in data["statutory_notice"]

    # 3. Verify cross-tenant institution protection
    # An institution from a different scope cannot extract another institution's document
    # Find a document belonging to a different institution than inst_admin (inst1: 1-100234501)
    other_doc = next(d for d in docs if d["institution_id"] != test_doc["institution_id"])
    denied_res = client.get(
        f"/api/documents/{other_doc['id']}/extract",
        headers={"Authorization": f"Bearer {inst_token}"}
    )
    # Must be 403 Forbidden
    assert denied_res.status_code == 403
