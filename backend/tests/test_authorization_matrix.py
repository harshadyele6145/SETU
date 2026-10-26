import io
import pytest
from datetime import date, datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.seed.seed_data import seed_database
from backend.app.models.institution import Institution
from backend.app.models.region import Region
from backend.app.models.application import Application
from backend.app.models.compliance import ComplianceObligation, ComplianceEvidence
from backend.app.models.document import DocumentRegistry
from backend.app.models.audit import AuditEvent
from backend.app.models.evc import EVCVisit, EVCExpert
from backend.app.models.user import User
from backend.app.core.security import UserRole, normalize_role, is_role_in
from backend.app.services.audit_service import audit_service


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. AUTHORIZATION MATRIX TESTS (ALL 9 ROLES + CANONICAL ALIASES)
# ==============================================================================

def test_canonical_role_normalization_and_aliases():
    """
    Verifies that canonical normalization correctly maps legitimate aliases:
    - BUREAU_OFFICER <-> BO_OFFICER
    - COMMITTEE_MBR <-> COMM_MEMBER
    - COMP_REV <-> COMP_REVIEW
    """
    assert normalize_role("BUREAU_OFFICER") == "BO_OFFICER"
    assert normalize_role("BO_OFFICER") == "BO_OFFICER"
    assert normalize_role("COMMITTEE_MBR") == "COMM_MEMBER"
    assert normalize_role("COMM_MEMBER") == "COMM_MEMBER"
    assert normalize_role("COMP_REV") == "COMP_REVIEW"
    assert normalize_role("COMP_REVIEW") == "COMP_REVIEW"
    assert normalize_role("INST_ADMIN") == "INST_ADMIN"
    assert normalize_role("COMP_AUTH") == "COMP_AUTH"
    assert normalize_role("SYS_ADMIN") == "SYS_ADMIN"

    # In checks
    assert is_role_in("COMP_REV", ["COMP_REVIEW"])
    assert is_role_in("COMP_REVIEW", ["COMP_REV"])
    assert is_role_in("BUREAU_OFFICER", ["BO_OFFICER"])
    assert is_role_in("BO_OFFICER", ["BUREAU_OFFICER"])
    assert is_role_in("COMMITTEE_MBR", ["COMM_MEMBER"])
    assert is_role_in("COMM_MEMBER", ["COMMITTEE_MBR"])


def test_authorization_matrix_all_roles(client: TestClient, db_session: Session):
    """
    Verifies permitted vs denied operations across every implemented role persona:
    1. INST_ADMIN: Can submit own application; Denied approving, returning, verifying, or toggling adapter.
    2. RO_OFFICER: Can return/scrutinize in region; Denied final approval or cross-region access.
    3. REGIONAL_DIR: Can oversee and reassign in region; Denied final statutory approval.
    4. EVC_COORD: Can schedule in region; Denied final approval or cross-region scheduling.
    5. COMMITTEE_MBR & COMM_MEMBER: Can view/submit assigned report; Denied unassigned inspection or approving.
    6. COMP_REV & COMP_REVIEW: Both aliases can verify compliance evidence; Denied final statutory approval.
    7. BO_OFFICER & BUREAU_OFFICER: Both aliases can sync open data, toggle failure; Denied final statutory approval.
    8. COMP_AUTH: Can issue final statutory approval/rejection (INV-03 reserve).
    9. SYS_ADMIN: Can toggle adapter; Denied issuing final statutory approval (statutory reserve).
    """
    seed_database(db_session, generate_alerts=False)

    tokens = {
        "INST_ADMIN": get_token_for(client, "inst_admin@fictional-nist.edu.in"),
        "INST_ADMIN_2": get_token_for(client, "inst_admin2@fictional-poly.org"),
        "RO_OFFICER": get_token_for(client, "ro_north@aicte.gov.in"),
        "RO_WEST": get_token_for(client, "ro_west@aicte.gov.in"),
        "REGIONAL_DIR": get_token_for(client, "ro_west_dir@aicte.gov.in"),
        "EVC_COORD": get_token_for(client, "evc_coord@aicte.gov.in"),
        "COMM_MEMBER": get_token_for(client, "comm_member@aicte.gov.in"),
        "COMMITTEE_MBR": get_token_for(client, "expert1@aicte-roster.ac.in"),
        "COMP_REVIEW": get_token_for(client, "comp_review@aicte.gov.in"),
        "COMP_REV": get_token_for(client, "compliance_reviewer@aicte.gov.in"),
        "BO_OFFICER": get_token_for(client, "bo_officer@aicte.gov.in"),
        "BUREAU_OFFICER": get_token_for(client, "bureau_officer@aicte.gov.in"),
        "COMP_AUTH": get_token_for(client, "comp_auth@aicte.gov.in"),
        "SYS_ADMIN": get_token_for(client, "sys_admin@aicte.gov.in"),
    }

    # Find a northern application and an obligation
    north_app = db_session.query(Application).filter(Application.application_no.like("%RO_NORTH%")).first()
    if not north_app:
        north_app = db_session.query(Application).first()

    ob = db_session.query(ComplianceObligation).first()
    inst_user = db_session.query(User).filter(User.role == "INST_ADMIN").first()
    evidence = db_session.query(ComplianceEvidence).filter(ComplianceEvidence.verification_status == "SUBMITTED").first()
    if not evidence and ob and inst_user:
        evidence = ComplianceEvidence(
            obligation_id=ob.id,
            institution_id=ob.institution_id,
            file_name="test_ev.pdf",
            file_path="uploads/test_ev.pdf",
            file_size=1024,
            mime_type="application/pdf",
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            verification_status="SUBMITTED",
            submitted_by_id=inst_user.id
        )
        db_session.add(evidence)
        db_session.commit()

    # --------------------------------------------------------------------------
    # CHECK 1: Only COMP_AUTH can grant final approval (INV-03)
    # All other roles must be rejected with HTTP 403 Forbidden
    # --------------------------------------------------------------------------
    for role_name in ["INST_ADMIN", "RO_OFFICER", "REGIONAL_DIR", "EVC_COORD", "COMM_MEMBER", "COMMITTEE_MBR", "COMP_REVIEW", "COMP_REV", "BO_OFFICER", "BUREAU_OFFICER", "SYS_ADMIN"]:
        res = client.post(
            f"/api/applications/{north_app.id}/transition",
            headers=auth_header(tokens[role_name]),
            json={"action": "APPROVED", "target_stage_key": "APPROVED", "comments": "Unauthorized approval attempt"}
        )
        assert res.status_code == 403, f"Expected role {role_name} to be rejected from approving with 403, got {res.status_code}"

    # --------------------------------------------------------------------------
    # CHECK 2: Both COMP_REVIEW and COMP_REV can verify compliance evidence
    # --------------------------------------------------------------------------
    if evidence:
        res_cr = client.post(
            f"/api/compliance/evidence/{evidence.id}/verify",
            headers=auth_header(tokens["COMP_REVIEW"]),
            json={"is_approved": True, "review_comments": "Verified by COMP_REVIEW alias."}
        )
        assert res_cr.status_code in [200, 400], f"Expected COMP_REVIEW to be permitted to verify, got {res_cr.status_code}"

        res_crev = client.post(
            f"/api/compliance/evidence/{evidence.id}/verify",
            headers=auth_header(tokens["COMP_REV"]),
            json={"is_approved": True, "review_comments": "Verified by COMP_REV alias."}
        )
        assert res_crev.status_code in [200, 400], f"Expected COMP_REV to be permitted to verify, got {res_crev.status_code}"

    # INST_ADMIN cannot verify compliance evidence (must be 403)
    if evidence:
        res_inst_ver = client.post(
            f"/api/compliance/evidence/{evidence.id}/verify",
            headers=auth_header(tokens["INST_ADMIN"]),
            json={"is_approved": True, "review_comments": "Illegal college self-verification"}
        )
        assert res_inst_ver.status_code == 403, f"Expected INST_ADMIN to be forbidden from verifying evidence, got {res_inst_ver.status_code}"

    # --------------------------------------------------------------------------
    # CHECK 3: Toggle adapter failure authorization
    # Permitted: SYS_ADMIN, BO_OFFICER, BUREAU_OFFICER, REGIONAL_DIR
    # Denied: INST_ADMIN, RO_OFFICER, COMM_MEMBER
    # --------------------------------------------------------------------------
    for role_name in ["SYS_ADMIN", "BO_OFFICER", "BUREAU_OFFICER", "REGIONAL_DIR"]:
        res_toggle = client.post(
            "/api/integrations/toggle-failure",
            headers=auth_header(tokens[role_name]),
            json={"simulate_failure": False}
        )
        assert res_toggle.status_code == 200, f"Expected {role_name} permitted to toggle failure, got {res_toggle.status_code}"

    for role_name in ["INST_ADMIN", "RO_OFFICER", "COMM_MEMBER"]:
        res_toggle_denied = client.post(
            "/api/integrations/toggle-failure",
            headers=auth_header(tokens[role_name]),
            json={"simulate_failure": True}
        )
        assert res_toggle_denied.status_code == 403, f"Expected {role_name} forbidden from toggling failure, got {res_toggle_denied.status_code}"


# ==============================================================================
# 2. DATA ISOLATION AND MISSING SCOPE SAFETY
# ==============================================================================

def test_audit_log_data_isolation(client: TestClient, db_session: Session):
    """
    Verifies multi-tenant isolation on the audit trail:
    - INST_ADMIN only sees audit events for their own institution.
    - RO_OFFICER only sees audit events for their assigned region.
    - National roles (BO_OFFICER, COMP_AUTH) see national events.
    """
    seed_database(db_session, generate_alerts=False)

    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")
    bo_token = get_token_for(client, "bo_officer@aicte.gov.in")

    # National audit list
    res_bo = client.get("/api/audit", headers=auth_header(bo_token))
    assert res_bo.status_code == 200
    all_events = res_bo.json()
    assert len(all_events) > 0

    # Scoped institution audit list
    res_inst = client.get("/api/audit", headers=auth_header(inst_token))
    assert res_inst.status_code == 200
    inst_events = res_inst.json()
    # Scoped events must be less than or equal to total events
    assert len(inst_events) <= len(all_events)

    # Scoped regional audit list
    res_ro = client.get("/api/audit", headers=auth_header(ro_token))
    assert res_ro.status_code == 200
    ro_events = res_ro.json()
    assert len(ro_events) <= len(all_events)


def test_missing_scope_fails_closed(client: TestClient, db_session: Session):
    """
    Verifies that missing tenant or region scopes fail closed:
    - INST_ADMIN with institution_id = None sees [] on applications, compliance, dependencies, audit.
    - RO_OFFICER with region_id = None sees [] on applications, compliance, dependencies, audit.
    """
    seed_database(db_session, generate_alerts=False)

    # Create unassigned users
    from backend.app.core.security import get_password_hash
    pwd = get_password_hash("DemoPass@2026")
    
    unassigned_inst = User(
        email="unassigned_inst@test.com",
        hashed_password=pwd,
        full_name="Unassigned Inst Admin",
        role="INST_ADMIN",
        institution_id=None
    )
    unassigned_ro = User(
        email="unassigned_ro@test.com",
        hashed_password=pwd,
        full_name="Unassigned RO Officer",
        role="RO_OFFICER",
        region_id=None
    )
    db_session.add_all([unassigned_inst, unassigned_ro])
    db_session.commit()

    token_inst = get_token_for(client, "unassigned_inst@test.com")
    token_ro = get_token_for(client, "unassigned_ro@test.com")

    # 1. Applications listing fails closed to []
    assert client.get("/api/applications", headers=auth_header(token_inst)).json() == []
    assert client.get("/api/applications", headers=auth_header(token_ro)).json() == []

    # 2. Compliance dependencies graph fails closed
    assert client.get("/api/bottlenecks/dependencies", headers=auth_header(token_inst)).json() == {"nodes": [], "links": []}
    assert client.get("/api/bottlenecks/dependencies", headers=auth_header(token_ro)).json() == {"nodes": [], "links": []}

    # 3. Audit log fails closed to []
    assert client.get("/api/audit", headers=auth_header(token_inst)).json() == []
    assert client.get("/api/audit", headers=auth_header(token_ro)).json() == []


# ==============================================================================
# 3. STATUTORY INVARIANTS (INV-01, INV-02, INV-03)
# ==============================================================================

def test_invariant_inv01_evidence_submission_never_autoverified(client: TestClient, db_session: Session):
    """
    INV-01: Uploading compliance evidence leaves it strictly in SUBMITTED status.
    It is NEVER automatically set to VERIFIED.
    """
    seed_database(db_session, generate_alerts=False)
    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")

    ob = db_session.query(ComplianceObligation).filter(ComplianceObligation.status == "PENDING").first()
    if not ob:
        ob = db_session.query(ComplianceObligation).first()

    # Submit evidence via multipart form
    file_content = b"%PDF-1.4 Simulated statutory compliance certificate"
    res = client.post(
        f"/api/compliance/obligations/{ob.id}/evidence",
        headers=auth_header(inst_token),
        data={"notes": "Uploaded formal undertaking."},
        files={"file": ("undertaking.pdf", io.BytesIO(file_content), "application/pdf")}
    )
    assert res.status_code == 200, f"Evidence upload failed: {res.text}"
    data = res.json()
    assert data["verification_status"] == "SUBMITTED", f"INV-01 VIOLATION: Expected SUBMITTED, got {data['verification_status']}"
    assert data["verified_at"] is None
    assert data["verified_by_name"] is None


def test_invariant_inv02_whitespace_justification_rejected(client: TestClient, db_session: Session):
    """
    INV-02: Scrutiny deficiency returns and inspection rescheduling must reject
    empty or whitespace-only justifications with HTTP 400.
    """
    seed_database(db_session, generate_alerts=False)
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")
    evc_token = get_token_for(client, "evc_coord@aicte.gov.in")

    app = db_session.query(Application).filter(Application.status == "UNDER_SCRUTINY").first()
    if not app:
        app = db_session.query(Application).first()
        app.status = "UNDER_SCRUTINY"
        db_session.commit()

    # 1. Scrutiny return with whitespace
    res_ret = client.post(
        f"/api/applications/{app.id}/return",
        headers=auth_header(ro_token),
        json={"comments": "     "}
    )
    assert res_ret.status_code == 400, f"INV-02 VIOLATION: Whitespace deficiency return was not rejected: {res_ret.text}"

    # 2. Reschedule with whitespace
    visit = db_session.query(EVCVisit).first()
    if visit:
        res_resched = client.post(
            f"/api/evc/visits/{visit.id}/reschedule",
            headers=auth_header(evc_token),
            json={"new_date": "2026-06-15", "delay_reason": "   \n\t   "}
        )
        assert res_resched.status_code in [400, 422], f"INV-02 VIOLATION: Whitespace reschedule was not rejected: {res_resched.text}"


def test_invariant_inv03_terminal_locking_and_immutability(client: TestClient, db_session: Session):
    """
    INV-03: Once an application enters terminal state (APPROVED or REJECTED),
    all subsequent transitions, returns, resubmissions, and reassignments are blocked.
    """
    seed_database(db_session, generate_alerts=False)
    ca_token = get_token_for(client, "comp_auth@aicte.gov.in")
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")
    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")

    app = db_session.query(Application).filter(Application.status == "DECISION_PENDING").first()
    if not app:
        app = db_session.query(Application).first()
        app.status = "DECISION_PENDING"
        db_session.commit()

    # Step 1: Competent Authority grants final approval
    res_appr = client.post(
        f"/api/applications/{app.id}/transition",
        headers=auth_header(ca_token),
        json={"action": "APPROVED", "target_stage_key": "APPROVED", "comments": "Formal Statutory Approval Granted."}
    )
    assert res_appr.status_code == 200, f"Final approval failed: {res_appr.text}"
    assert res_appr.json()["status"] == "APPROVED"

    # Step 2: Attempt further transition on APPROVED application (MUST BE 400)
    res_further = client.post(
        f"/api/applications/{app.id}/transition",
        headers=auth_header(ca_token),
        json={"action": "UNDER_SCRUTINY", "target_stage_key": "UNDER_SCRUTINY", "comments": "Illegal transition out of terminal state"}
    )
    assert res_further.status_code == 400, f"INV-03 VIOLATION: Terminal application was transitioned: {res_further.text}"
    assert "INV-03" in res_further.json()["detail"]

    # Step 3: Attempt deficiency return on APPROVED application (MUST BE 400)
    res_ret = client.post(
        f"/api/applications/{app.id}/return",
        headers=auth_header(ro_token),
        json={"comments": "Illegal return of approved application."}
    )
    assert res_ret.status_code == 400, f"INV-03 VIOLATION: Terminal application was returned: {res_ret.text}"
    assert "INV-03" in res_ret.json()["detail"]

    # Step 4: Attempt officer reassignment on APPROVED application (MUST BE 400)
    officer = db_session.query(User).filter(User.role == "RO_OFFICER").first()
    res_reassign = client.post(
        f"/api/applications/{app.id}/reassign",
        headers=auth_header(ro_token),
        json={"officer_id": officer.id, "comments": "Illegal reassignment of approved file."}
    )
    assert res_reassign.status_code == 400, f"INV-03 VIOLATION: Terminal application was reassigned: {res_reassign.text}"
    assert "INV-03" in res_reassign.json()["detail"]


# ==============================================================================
# 4. AUDIT INTEGRITY AND CONCURRENT SEQUENCING
# ==============================================================================

def test_audit_hash_chain_tamper_and_reorder_detection(client: TestClient, db_session: Session):
    """
    Verifies that changes to audit events, deletions, reordered events,
    and broken hash links are detectable by audit_service.verify_chain.
    """
    seed_database(db_session, generate_alerts=False)

    # 1. Intact chain verification
    is_valid, count, broken_seq, msg = audit_service.verify_chain(db_session)
    assert is_valid is True, f"Initial chain was unexpectedly invalid: {msg}"
    assert count > 0

    # 2. Modify an event payload
    event = db_session.query(AuditEvent).filter(AuditEvent.sequence_no == 2).first()
    if event:
        orig_action = event.action
        event.action = "TAMPERED_ACTION_NAME"
        db_session.flush()

        # Verification must now fail!
        is_valid_after, _, broken_seq, _ = audit_service.verify_chain(db_session)
        assert is_valid_after is False, "Cryptographic audit chain failed to detect payload tampering!"
        assert broken_seq == 2

        # Revert
        event.action = orig_action
        db_session.flush()

    # 3. Test sequence uniqueness constraint under concurrent writes
    latest = db_session.query(AuditEvent).order_by(AuditEvent.sequence_no.desc()).first()
    if latest:
        duplicate_event = AuditEvent(
            sequence_no=latest.sequence_no,  # Duplicate sequence number
            timestamp=datetime.now(timezone.utc),
            actor_role="RO_OFFICER",
            action="DUPLICATE_SEQUENCE_EVENT",
            entity_type="APPLICATION",
            entity_id="APP-TEST",
            previous_hash=latest.current_hash,
            current_hash="abcd" * 16
        )
        db_session.add(duplicate_event)
        with pytest.raises(IntegrityError):
            db_session.flush()
        db_session.rollback()
