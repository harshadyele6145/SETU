# SETU — Engineering Progress & Milestone Tracking

## Session Date: 2026-10-25
**Branch:** `master`  
**Completed Milestones:**
- Milestone 1 — Foundation
- Milestone 2 — Authentication and Data Model (P0)
- Milestone 3 — Workflow Engine & Cryptographic Audit Ledger (P0)

---

## 1. Work Completed in Milestone 3
- Implemented full multi-route approval workflow engine (`backend/app/services/workflow_engine.py`):
  - Route A (Only Scrutiny): Submission -> Scrutiny -> Regional Review -> Decision Pending -> Competent Authority Decision
  - Route B (Scrutiny + EVC): Scrutiny -> EVC Queue -> Scheduled -> Inspection Report -> Decision Pending
  - Route C (EVC + SAC/SHC): EVC Deficiencies -> SHC Hearing -> SAC Appeal -> Decision Pending
  - Route D (Only EVC): Mandated Inspection Queue -> Visit Conducted -> Report Review -> Decision Pending
- Implemented state transition rules and role permissions (`STAGE_ROLE_PERMISSIONS`).
- Enforced mandatory deficiency reason requirement (`INV-02`) when returning an application.
- Enforced statutory authority guard (`INV-03`): Only Competent Authority (`COMP_AUTH`) can approve or reject applications; unauthorized attempts return 403 Forbidden.
- Implemented clarification resubmission incrementing `return_count` for tracking in Exception Cockpit.
- Implemented officer reassignment and application movement history.
- Implemented REST API endpoints in `backend/app/api/applications.py`:
  - `GET /api/applications` (with route, status, region, institution filters and scope enforcement)
  - `POST /api/applications`
  - `GET /api/applications/{id}` (returns complete case details and chronological history)
  - `POST /api/applications/{id}/submit`
  - `POST /api/applications/{id}/transition`
  - `POST /api/applications/{id}/return`
  - `POST /api/applications/{id}/resubmit`
  - `POST /api/applications/{id}/reassign`
  - `GET /api/applications/{id}/timeline`
- Implemented Audit REST endpoints in `backend/app/api/audit.py`:
  - `GET /api/audit` (paginated list of audit events)
  - `GET /api/audit/verify-chain` (verifies SHA-256 hash-chain integrity across the whole database)
- Expanded synthetic seed data in `seed_data.py` to 26 diverse applications covering all 4 route patterns and varied stages.
- Authored and verified one-command reset-and-seed script (`backend/seed/reset_and_seed.py`) with safety guard against non-demo environments.
- Implemented interactive frontend pages:
  - `frontend/src/pages/ApplicationsPage.tsx`: Filterable table with contextual workflow buttons, deficiency return modal dialog, and resubmission.
  - `frontend/src/pages/TimelinePage.tsx`: Case selector, metadata cards, and chronological movement ledger.
  - `frontend/src/pages/AuditTrailPage.tsx`: Cryptographic status banner, "Verify Cryptographic Hash Chain" live button, and tamper-evident event table.
- Verified frontend compilation (`npm run build`).
- Wrote and executed automated tests in `test_workflow.py` and `test_audit_hashchain.py`, testing complete lifecycle, mandatory return reasons, forbidden transitions, cross-region rejections, valid hash-chain verification, and intentional database tamper detection.

---

## 2. Commands Executed & Results
| Command | Purpose | Result / Exit Code |
|---|---|---|
| `python backend/seed/reset_and_seed.py` | Reset DB and seed 26 applications | Exit 0 (Success, 26 apps seeded) |
| `pytest backend/tests/test_workflow.py backend/tests/test_audit_hashchain.py` | Test workflow transitions & audit chain | Exit 0 (6 passed in 4.79s) |
| `pytest` | Run full test suite (Milestone 3) | Exit 0 (16 passed in 6.83s) |
| `pytest backend/tests/test_compliance.py backend/tests/test_documents.py` | Test compliance obligations & document registry | Exit 0 (5 passed in 3.12s) |
| `pytest` | Run full test suite (Milestone 4) | Exit 0 (21 passed in 11.06s) |
| `npm run build --prefix frontend` | Compile production frontend bundle (Milestone 4) | Exit 0 (Success, dist generated) |

---

## 3. Milestone 4 Completed: Compliance Obligations & Document Registry (P0)
- **ComplianceService**: Digital tracking of undertakings and conditions precedent. Enforces invariant INV-01: uploaded evidence enters `SUBMITTED`, never automatically `VERIFIED`.
- **Two-Step Verification**: Requires review by an authorized AICTE officer (`RO_OFFICER`, `BO_OFFICER`, `COMP_REVIEW`) with mandatory review notes. Supports deficiency rejection and resubmission.
- **DocumentService**: Prescribed Document Registry managing registered lease deeds, municipal fire NOCs, and building safety certificates with validity windows.
- **Renewal Versioning**: Renewal upload sets original to `SUPERSEDED`, links `previous_document_id`, sets replacement version `v(N+1)`, and holds state in `RENEWAL_SUBMITTED` until authorized review.
- **Protected Downloads**: Direct file download endpoint `GET /api/documents/{id}/download` enforcing strict record-level scoping (cannot access other institutions' documents).
- **Frontend Pages**: Complete UI implementations in `frontend/src/pages/CompliancePage.tsx` and `frontend/src/pages/DocumentsPage.tsx`.

---

## 4. Known Defects & Limitations
- Automated alert generation (windows: 30, 15, 7, 1 day, overdue) and escalation queue are queued for Milestone 5.
- Full EVC expert coordination workflow is scheduled for Milestone 6.

---

## 5. Next Steps
- Execute Milestone 5: Implement Deadline and Alert Engine (P0), compound idempotency, downtime catch-up, notification outbox, and escalation management.

