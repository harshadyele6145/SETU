import io
from fastapi.testclient import TestClient
from backend.seed.seed_data import seed_database
from backend.app.models.institution import Institution
from backend.app.models.document import DocumentRegistry


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    return res.json()["access_token"]


def test_document_registration_and_renewal_lifecycle(client: TestClient, db_session):
    seed_database(db_session)

    inst1_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")
    inst1 = db_session.query(Institution).filter(Institution.aicte_id == "1-100234501").first()

    # 1. Register initial Lease Deed (Version 1)
    file_bytes_v1 = b"%PDF-1.4 initial registered lease deed valid until 2026"
    doc_res = client.post(
        "/api/documents",
        headers={"Authorization": f"Bearer {inst1_token}"},
        data={
            "institution_id": inst1.id,
            "document_category": "LEASE_DEED",
            "title": "Registered Campus Land Lease Deed",
            "issue_date": "1996-05-10",
            "expiry_date": "2026-11-01"
        },
        files={"file": ("lease_deed_v1.pdf", io.BytesIO(file_bytes_v1), "application/pdf")}
    )
    assert doc_res.status_code == 201
    doc_v1 = doc_res.json()
    assert doc_v1["current_version"] == 1
    assert len(doc_v1["sha256_hash"]) == 64
    old_doc_id = doc_v1["id"]

    # 2. Institution submits Renewal Replacement (Version 2)
    file_bytes_v2 = b"%PDF-1.4 renewed registered lease deed valid until 2056"
    renew_res = client.post(
        f"/api/documents/{old_doc_id}/renew",
        headers={"Authorization": f"Bearer {inst1_token}"},
        data={
            "issue_date": "2026-10-01",
            "expiry_date": "2056-10-01"
        },
        files={"file": ("lease_deed_v2_renewed.pdf", io.BytesIO(file_bytes_v2), "application/pdf")}
    )
    assert renew_res.status_code == 200
    doc_v2 = renew_res.json()

    # Invariant: Renewal increments version and links previous document
    assert doc_v2["current_version"] == 2
    assert doc_v2["previous_document_id"] == old_doc_id
    # Invariant: Replacement submission does NOT automatically make it VALID
    assert doc_v2["status"] == "RENEWAL_SUBMITTED"

    # Old document should now be marked SUPERSEDED
    old_doc_db = db_session.get(DocumentRegistry, old_doc_id)
    assert old_doc_db.status == "SUPERSEDED"

    # 3. Regional Officer reviews and verifies renewal document
    verify_res = client.post(
        f"/api/documents/{doc_v2['id']}/verify",
        headers={"Authorization": f"Bearer {ro_token}"},
        json={"is_verified": True, "comments": "Registered lease deed renewal verified with Sub-Registrar seal."}
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "VALID"


def test_protected_document_download_authorization(client: TestClient, db_session):
    seed_database(db_session)

    inst1_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    inst2_token = get_token_for(client, "inst_admin2@fictional-poly.org")
    inst1 = db_session.query(Institution).filter(Institution.aicte_id == "1-100234501").first()

    # Upload document for Inst 1
    file_bytes = b"%PDF-1.4 confidential fire clearance record"
    doc_res = client.post(
        "/api/documents",
        headers={"Authorization": f"Bearer {inst1_token}"},
        data={
            "institution_id": inst1.id,
            "document_category": "FIRE_NOC",
            "title": "Fire Clearance 2026",
            "issue_date": "2026-01-01",
            "expiry_date": "2027-01-01"
        },
        files={"file": ("fire_noc.pdf", io.BytesIO(file_bytes), "application/pdf")}
    )
    doc_id = doc_res.json()["id"]

    # Authorized download by owning institution succeeds
    own_download = client.get(f"/api/documents/{doc_id}/download", headers={"Authorization": f"Bearer {inst1_token}"})
    assert own_download.status_code == 200
    assert b"confidential fire clearance record" in own_download.content

    # Unauthorized download by another institution is rejected (403 Forbidden)
    cross_download = client.get(f"/api/documents/{doc_id}/download", headers={"Authorization": f"Bearer {inst2_token}"})
    assert cross_download.status_code == 403
    assert "Security violation" in cross_download.json()["detail"]

