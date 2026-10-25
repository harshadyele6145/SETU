import io
from fastapi.testclient import TestClient
from backend.seed.seed_data import seed_database
from backend.app.models.institution import Institution
from backend.app.models.compliance import ComplianceObligation


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    return res.json()["access_token"]


def test_evidence_submission_distinct_from_verification(client: TestClient, db_session):
    seed_database(db_session)

    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    reviewer_token = get_token_for(client, "comp_review@aicte.gov.in")

    inst = db_session.query(Institution).filter(Institution.aicte_id == "1-100234501").first()

    # 1. Create a compliance obligation
    ob_res = client.post(
        "/api/compliance/obligations",
        headers={"Authorization": f"Bearer {reviewer_token}"},
        json={
            "institution_id": inst.id,
            "category": "FIRE_SAFETY",
            "title": "Municipal Fire NOC Renewal",
            "description": "Submit updated Fire Safety clearance certificate.",
            "due_date": "2026-12-31",
            "condition_source": "APH Chapter I Norms"
        }
    )
    assert ob_res.status_code == 201
    ob_id = ob_res.json()["id"]

    # 2. Institution submits evidence file
    dummy_pdf = io.BytesIO(b"%PDF-1.4 simulated fire noc evidence bytes for compliance test")
    upload_res = client.post(
        f"/api/compliance/obligations/{ob_id}/evidence",
        headers={"Authorization": f"Bearer {inst_token}"},
        files={"file": ("fire_noc_2026.pdf", dummy_pdf, "application/pdf")},
        data={"notes": "Uploaded valid Fire Safety certificate renewed by Kanpur Nagar Nigam."}
    )
    assert upload_res.status_code == 200
    evidence_data = upload_res.json()
    evidence_id = evidence_data["id"]

    # Critical Invariant INV-01: Submission NEVER automatically verifies compliance
    assert evidence_data["verification_status"] == "SUBMITTED"
    assert evidence_data["verified_by_name"] is None

    # Verify obligation status is SUBMITTED, NOT VERIFIED
    ob_check = client.get(f"/api/compliance/obligations/{ob_id}", headers={"Authorization": f"Bearer {inst_token}"})
    assert ob_check.json()["status"] == "SUBMITTED"

    # 3. Compliance Reviewer formally reviews and verifies evidence
    verify_res = client.post(
        f"/api/compliance/evidence/{evidence_id}/verify",
        headers={"Authorization": f"Bearer {reviewer_token}"},
        json={"is_approved": True, "review_comments": "Verified valid until Dec 2027 by Chief Fire Officer."}
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["verification_status"] == "VERIFIED"

    # Confirm obligation is now VERIFIED
    ob_final = client.get(f"/api/compliance/obligations/{ob_id}", headers={"Authorization": f"Bearer {inst_token}"})
    assert ob_final.json()["status"] == "VERIFIED"


def test_compliance_evidence_deficiency_and_comments(client: TestClient, db_session):
    seed_database(db_session)

    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    reviewer_token = get_token_for(client, "comp_review@aicte.gov.in")
    inst = db_session.query(Institution).filter(Institution.aicte_id == "1-100234501").first()

    ob_res = client.post(
        "/api/compliance/obligations",
        headers={"Authorization": f"Bearer {reviewer_token}"},
        json={
            "institution_id": inst.id,
            "category": "FACULTY_RATIO",
            "title": "Faculty-Student Ratio Compliance",
            "description": "Submit certified cadre payroll proof.",
            "due_date": "2026-11-15",
            "condition_source": "APH Condition"
        }
    )
    ob_id = ob_res.json()["id"]

    dummy_doc = io.BytesIO(b"dummy faculty payroll document")
    upload_res = client.post(
        f"/api/compliance/obligations/{ob_id}/evidence",
        headers={"Authorization": f"Bearer {inst_token}"},
        files={"file": ("faculty_list.pdf", dummy_doc, "application/pdf")},
        data={"notes": "Current faculty cadre sheet."}
    )
    ev_id = upload_res.json()["id"]

    # Reviewer rejects with deficiency comments
    reject_res = client.post(
        f"/api/compliance/evidence/{ev_id}/verify",
        headers={"Authorization": f"Bearer {reviewer_token}"},
        json={"is_approved": False, "review_comments": "Professor cadre ratio is 1:3 instead of prescribed 1:2. Provide appointment letters for 2 professors."}
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["verification_status"] == "DEFICIENT"
    assert "Provide appointment letters" in reject_res.json()["rejection_reason"]


def test_cross_institution_evidence_submission_rejected(client: TestClient, db_session):
    seed_database(db_session)

    inst2_token = get_token_for(client, "inst_admin2@fictional-poly.org")  # Institution 2
    reviewer_token = get_token_for(client, "comp_review@aicte.gov.in")
    inst1 = db_session.query(Institution).filter(Institution.aicte_id == "1-100234501").first()

    ob_res = client.post(
        "/api/compliance/obligations",
        headers={"Authorization": f"Bearer {reviewer_token}"},
        json={
            "institution_id": inst1.id,
            "category": "BARRIER_FREE",
            "title": "Ramp & Lift Construction",
            "description": "Evidence of barrier-free access.",
            "due_date": "2026-12-01",
            "condition_source": "APH Norms"
        }
    )
    ob_id = ob_res.json()["id"]

    # Inst Admin 2 attempts to upload evidence for Inst 1's obligation
    dummy_doc = io.BytesIO(b"malicious cross-institution upload attempt")
    cross_upload = client.post(
        f"/api/compliance/obligations/{ob_id}/evidence",
        headers={"Authorization": f"Bearer {inst2_token}"},
        files={"file": ("evidence.pdf", dummy_doc, "application/pdf")},
        data={"notes": "Hacked submission"}
    )
    assert cross_upload.status_code == 403
    assert "Security violation" in cross_upload.json()["detail"]

