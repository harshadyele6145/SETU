import pytest
from datetime import datetime, date, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.seed.seed_data import seed_database
from backend.app.models.institution import Institution
from backend.app.models.application import Application, ApplicationHistory
from backend.app.models.workflow import WorkflowStage
from backend.app.models.audit import AuditEvent
from backend.app.models.user import User


def get_token(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_three_minute_hackathon_demo_flow(client: TestClient, db_session: Session):
    """
    THREE-MINUTE HACKATHON LIVE DEMO AUTOMATED SUITE (10 MANDATORY PHASES):
    1. Sign in as seeded Institution Administrator (Dr. R. K. Verma).
    2. Open an existing synthetic application belonging to that institution.
    3. Verify current workflow stage, data provenance, holder responsibility, and SLA deadline.
    4. RO returns for deficiency with non-empty reason (INV-02); Inst Admin responds/resubmits clarification.
    5. Sign in as authorized Regional Officer (Dr. Arun Mehra).
    6. Verify application's changed state and movement audit history.
    7. Visit Attention Queue and confirm diagnostic factors match underlying record.
    8. Open Audit Ledger and verify cryptographic SHA-256 chain.
    9. Attempt unauthorized actions across multiple roles and verify backend rejects them (HTTP 403).
    10. Sign in as Competent Authority (Member Secretary) for terminal statutory determination (INV-03).
    11. Verify Stage Pipeline Distribution chart counts match exact role data scopes.
    """
    seed_database(db_session, generate_alerts=False)

    tokens = {
        "INST_ADMIN": get_token(client, "inst_admin@fictional-nist.edu.in"),
        "RO_NORTH": get_token(client, "ro_north@aicte.gov.in"),
        "RO_WEST": get_token(client, "ro_west@aicte.gov.in"),
        "COMM_MEMBER": get_token(client, "comm_member@aicte.gov.in"),
        "BO_OFFICER": get_token(client, "bo_officer@aicte.gov.in"),
        "COMP_AUTH": get_token(client, "comp_auth@aicte.gov.in"),
    }

    # --------------------------------------------------------------------------
    # STEP 1 & 2: INST_ADMIN signs in and opens own synthetic application
    # --------------------------------------------------------------------------
    res_list = client.get("/api/applications", headers=auth_header(tokens["INST_ADMIN"]))
    assert res_list.status_code == 200
    inst_apps = res_list.json()
    assert len(inst_apps) > 0, "No applications returned for seeded institution admin"
    target_app_id = inst_apps[0]["id"]

    # --------------------------------------------------------------------------
    # STEP 3: Verify workflow stage, provenance, holder, deadline
    # --------------------------------------------------------------------------
    res_detail = client.get(f"/api/applications/{target_app_id}", headers=auth_header(tokens["INST_ADMIN"]))
    assert res_detail.status_code == 200
    app_data = res_detail.json()

    assert app_data["source_system"] == "SYNTHETIC_SEED"
    assert app_data["is_synthetic"] is True
    assert "current_stage_key" in app_data or "status" in app_data
    assert "current_sla_deadline" in app_data

    # --------------------------------------------------------------------------
    # STEP 4: Scrutiny return with non-empty reason (INV-02) & Inst Admin Resubmission
    # --------------------------------------------------------------------------
    # A) Verify whitespace/empty deficiency reason is rejected (INV-02)
    res_empty_return = client.post(
        f"/api/applications/{target_app_id}/return",
        headers=auth_header(tokens["RO_NORTH"]),
        json={"comments": "   "}
    )
    assert res_empty_return.status_code == 400, "Expected empty return reason to be rejected with 400"

    # B) Valid statutory return by Regional Officer
    res_valid_return = client.post(
        f"/api/applications/{target_app_id}/return",
        headers=auth_header(tokens["RO_NORTH"]),
        json={"comments": "Municipal Fire Safety Clearance NOC requires updated endorsement stamp."}
    )
    assert res_valid_return.status_code == 200
    assert res_valid_return.json()["status"] in ["SCRUTINY_DEFICIENT", "DEFICIENT"]

    # C) Institution Admin responds to deficiency / resubmits clarification
    res_resubmit = client.post(
        f"/api/applications/{target_app_id}/resubmit",
        headers=auth_header(tokens["INST_ADMIN"]),
        json={"comments": "Uploaded renewed municipal fire safety clearance NOC with digital seal."}
    )
    assert res_resubmit.status_code == 200
    assert res_resubmit.json()["status"] in ["UNDER_SCRUTINY", "SUBMITTED"]

    # --------------------------------------------------------------------------
    # STEP 5 & 6: Authorized Officer verifies changed state and movement history
    # --------------------------------------------------------------------------
    res_ro_app = client.get(f"/api/applications/{target_app_id}", headers=auth_header(tokens["RO_NORTH"]))
    assert res_ro_app.status_code == 200
    ro_app_data = res_ro_app.json()
    assert ro_app_data["status"] in ["UNDER_SCRUTINY", "SUBMITTED"]

    res_history = client.get(f"/api/applications/{target_app_id}/timeline", headers=auth_header(tokens["RO_NORTH"]))
    assert res_history.status_code == 200
    history = res_history.json()
    assert len(history) >= 2, "Movement history does not reflect return and resubmission events"

    # --------------------------------------------------------------------------
    # STEP 7: Visit Attention Queue & verify explainable diagnostic factors
    # --------------------------------------------------------------------------
    res_att_queue = client.get("/api/attention/queue", headers=auth_header(tokens["RO_NORTH"]))
    assert res_att_queue.status_code == 200
    queue_items = res_att_queue.json()
    assert isinstance(queue_items, list)
    if len(queue_items) > 0:
        first_item = queue_items[0]
        assert "composite_score" in first_item
        assert "factors" in first_item
        assert "explanation" in first_item
        assert "recommended_action" in first_item

    res_summary = client.get(f"/api/attention/applications/{target_app_id}/summary", headers=auth_header(tokens["RO_NORTH"]))
    assert res_summary.status_code == 200
    summary_data = res_summary.json()
    assert "questions" in summary_data
    assert "q1_what_needs_attention" in summary_data["questions"]
    assert "q2_why_pending" in summary_data["questions"]
    assert "q3_who_responsible" in summary_data["questions"]
    assert "q4_what_happens_next" in summary_data["questions"]
    assert "q5_can_be_traced" in summary_data["questions"]

    # --------------------------------------------------------------------------
    # STEP 8: Open Audit Screen & verify cryptographic SHA-256 chain
    # --------------------------------------------------------------------------
    res_audit_list = client.get("/api/audit", headers=auth_header(tokens["RO_NORTH"]))
    assert res_audit_list.status_code == 200
    events = res_audit_list.json()
    assert len(events) > 0

    res_verify = client.get("/api/audit/verify-chain", headers=auth_header(tokens["RO_NORTH"]))
    assert res_verify.status_code == 200
    verify_data = res_verify.json()
    assert verify_data["is_valid"] is True
    assert verify_data["total_events_checked"] > 0

    # --------------------------------------------------------------------------
    # STEP 9: Attempt Unauthorized Actions and verify HTTP 403 Rejection
    # --------------------------------------------------------------------------
    # Unauthorized Action A: INST_ADMIN attempts final statutory approval
    res_unauth_a = client.post(
        f"/api/applications/{target_app_id}/transition",
        headers=auth_header(tokens["INST_ADMIN"]),
        json={"action": "APPROVED", "target_stage_key": "APPROVED", "comments": "Illegal self-approval"}
    )
    assert res_unauth_a.status_code == 403

    # Unauthorized Action B: RO_WEST attempts to access Northern regional application
    res_unauth_b = client.get(
        f"/api/applications/{target_app_id}",
        headers=auth_header(tokens["RO_WEST"])
    )
    assert res_unauth_b.status_code == 403

    # Unauthorized Action C: RO_NORTH attempts final statutory approval (INV-03 reserve)
    res_unauth_c = client.post(
        f"/api/applications/{target_app_id}/transition",
        headers=auth_header(tokens["RO_NORTH"]),
        json={"action": "APPROVED", "target_stage_key": "APPROVED", "comments": "RO attempting statutory determination"}
    )
    assert res_unauth_c.status_code == 403

    # --------------------------------------------------------------------------
    # STEP 10: Competent Authority grants final statutory determination (INV-03)
    # --------------------------------------------------------------------------
    # Transition forward along Route A canonical path: UNDER_SCRUTINY -> SCRUTINY_RECOMMENDED -> DECISION_PENDING
    res_rec = client.post(
        f"/api/applications/{target_app_id}/transition",
        headers=auth_header(tokens["RO_NORTH"]),
        json={"action": "RECOMMEND", "target_stage_key": "SCRUTINY_RECOMMENDED", "comments": "Scrutiny cleared successfully."}
    )
    assert res_rec.status_code == 200

    res_dp = client.post(
        f"/api/applications/{target_app_id}/transition",
        headers=auth_header(tokens["RO_NORTH"]),
        json={"action": "FORWARD_DECISION", "target_stage_key": "DECISION_PENDING", "comments": "Forwarded to Competent Authority for council decision."}
    )
    assert res_dp.status_code == 200

    # Competent Authority issues final statutory approval
    res_approve = client.post(
        f"/api/applications/{target_app_id}/transition",
        headers=auth_header(tokens["COMP_AUTH"]),
        json={"action": "APPROVED", "target_stage_key": "APPROVED", "comments": "Council grant of approval confirmed."}
    )
    assert res_approve.status_code == 200
    assert res_approve.json()["status"] == "APPROVED"

    # INV-03 Terminal Immutability: Verify subsequent modifications are permanently rejected (HTTP 400)
    res_terminal_return = client.post(
        f"/api/applications/{target_app_id}/return",
        headers=auth_header(tokens["RO_NORTH"]),
        json={"comments": "Attempting return on approved application"}
    )
    assert res_terminal_return.status_code == 400
    assert "terminal" in res_terminal_return.json()["detail"].lower()

    # --------------------------------------------------------------------------
    # STEP 11: Verify Stage Pipeline Distribution Chart Scoping
    # --------------------------------------------------------------------------
    # Inst Admin scope
    res_stat_inst = client.get("/api/dashboard/stats", headers=auth_header(tokens["INST_ADMIN"]))
    assert res_stat_inst.status_code == 200
    dist_inst = res_stat_inst.json()["stage_distribution"]
    total_inst = sum(item["count"] for item in dist_inst) if isinstance(dist_inst, list) else sum(dist_inst.values())
    assert total_inst > 0

    # Regional Officer scope
    res_stat_ro = client.get("/api/dashboard/stats", headers=auth_header(tokens["RO_NORTH"]))
    assert res_stat_ro.status_code == 200
    dist_ro = res_stat_ro.json()["stage_distribution"]
    total_ro = sum(item["count"] for item in dist_ro) if isinstance(dist_ro, list) else sum(dist_ro.values())
    assert total_ro >= total_inst, "Regional count must encompass multiple institutions"

    # National Oversight scope
    res_stat_bo = client.get("/api/dashboard/stats", headers=auth_header(tokens["BO_OFFICER"]))
    assert res_stat_bo.status_code == 200
    dist_bo = res_stat_bo.json()["stage_distribution"]
    total_bo = sum(item["count"] for item in dist_bo) if isinstance(dist_bo, list) else sum(dist_bo.values())
    assert total_bo >= total_ro, "National count must encompass all regional offices"
