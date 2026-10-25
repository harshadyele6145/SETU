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
| `pytest` | Run full test suite | Exit 0 (16 passed in 6.83s) |
| `npm run build --prefix frontend` | Compile production frontend bundle | Exit 0 (Success, 4.50s) |

---

## 3. Known Defects & Limitations
- Full EVC coordination (scheduling experts roster, report upload) and compliance obligations verification are scheduled for Milestones 4 and 6.

---

## 4. Next Steps
- Execute Milestone 4: Implement Compliance Obligations & Prescribed Document Registry (P0), evidence upload, two-step verification, lease renewal workflow, and checksum integrity.
