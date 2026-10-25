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

| `pytest backend/tests/test_deadlines.py backend/tests/test_alerts.py` | Test deadline calculator & idempotent alert engine | Exit 0 (7 passed in 5.82s) |
| `pytest` | Run full test suite (Milestone 5) | Exit 0 (28 passed in 20.95s) |
| `npm run build --prefix frontend` | Compile production frontend bundle (Milestone 5) | Exit 0 (Success, 7.54s) |
| `python backend/seed/reset_and_seed.py` | Reset DB and seed 26 apps + 35 alerts | Exit 0 (Success, 35 alerts, hash chain verified) |

---

## 3. Milestone 4 Completed: Compliance Obligations & Document Registry (P0)
- **ComplianceService**: Digital tracking of undertakings and conditions precedent. Enforces invariant INV-01: uploaded evidence enters `SUBMITTED`, never automatically `VERIFIED`.
- **Two-Step Verification**: Requires review by an authorized AICTE officer (`RO_OFFICER`, `BO_OFFICER`, `COMP_REVIEW`) with mandatory review notes. Supports deficiency rejection and resubmission.
- **DocumentService**: Prescribed Document Registry managing registered lease deeds, municipal fire NOCs, and building safety certificates with validity windows.
- **Renewal Versioning**: Renewal upload sets original to `SUPERSEDED`, links `previous_document_id`, sets replacement version `v(N+1)`, and holds state in `RENEWAL_SUBMITTED` until authorized review.
- **Protected Downloads**: Direct file download endpoint `GET /api/documents/{id}/download` enforcing strict record-level scoping (cannot access other institutions' documents).
- **Frontend Pages**: Complete UI implementations in `frontend/src/pages/CompliancePage.tsx` and `frontend/src/pages/DocumentsPage.tsx`.

---

## 4. Milestone 5 Completed: Deadline and Alert Engine (P0)
- **DeadlineService**: Calculation of application stage age, business days (skipping weekends and Gazetted Indian holidays), remaining time to SLA, compliance due dates, and document validity expirations.
- **Idempotency Guarantee**: Compound idempotency keys (`f"{entity_type}:{entity_id}:{alert_type}:{window_day}"`) prevent duplicate alerts on repeated evaluator runs. Verified in automated test.
- **Transactional Notification Outbox**: Enqueues alerts for email simulation and in-app feeds (`NotificationOutbox`).
- **Retry Mechanism & Failure Handling**: Automatic retries with exponential backoff and max retry threshold (3 attempts); failures transition to `FAILED` with explicit error diagnostics.
- **Downtime Recovery Simulator**: Evaluates active dataset against simulated future timestamps, catching up on all missed alert windows idempotently without creating duplicate records.
- **Scope-Enforced Alert Inbox**: Institutions only see and acknowledge alerts belonging to their institution; officers see regional or national alerts; cross-institution acknowledgments are strictly rejected with HTTP 403.
- **Frontend Pages**: Complete UI implementations in `frontend/src/pages/AlertsPage.tsx` and `frontend/src/pages/NotificationRecoveryPage.tsx`.

| `pytest backend/tests/test_evc.py backend/tests/test_dashboard.py` | Test EVC workflow, dynamic dashboard metrics & CSV export | Exit 0 (4 passed in 3.57s) |
| `pytest backend/tests/test_p0_mandatory_gate.py` | Run Mandatory P0 End-to-End Gate verification | Exit 0 (1 passed in 1.84s) |
| `pytest` | Run full test suite (Milestone 6) | Exit 0 (33 passed in 24.37s) |
| `npm run build --prefix frontend` | Compile production frontend bundle (Milestone 6) | Exit 0 (Success, 14.52s) |

---

## 4. Milestone 5 Completed: Deadline and Alert Engine (P0)
- **DeadlineService**: Calculation of application stage age, business days (skipping weekends and Gazetted Indian holidays), remaining time to SLA, compliance due dates, and document validity expirations.
- **Idempotency Guarantee**: Compound idempotency keys (`f"{entity_type}:{entity_id}:{alert_type}:{window_day}"`) prevent duplicate alerts on repeated evaluator runs. Verified in automated test.
- **Transactional Notification Outbox**: Enqueues alerts for email simulation and in-app feeds (`NotificationOutbox`).
- **Retry Mechanism & Failure Handling**: Automatic retries with exponential backoff and max retry threshold (3 attempts); failures transition to `FAILED` with explicit error diagnostics.
- **Downtime Recovery Simulator**: Evaluates active dataset against simulated future timestamps, catching up on all missed alert windows idempotently without creating duplicate records.
- **Scope-Enforced Alert Inbox**: Institutions only see and acknowledge alerts belonging to their institution; officers see regional or national alerts; cross-institution acknowledgments are strictly rejected with HTTP 403.
- **Frontend Pages**: Complete UI implementations in `frontend/src/pages/AlertsPage.tsx` and `frontend/src/pages/NotificationRecoveryPage.tsx`.

---

## 5. Milestone 6 Completed: EVC Management & Real-Time Operational Dashboard (P1)
- **EVCService**: Physical campus inspection lifecycle: visit scheduling, confirmed dates, expert roster assignment (`EVCExpert`), and signed report submission with SHA-256 integrity verification.
- **Mandatory Delay Logging**: Rescheduling strictly rejects empty or whitespace justifications with HTTP 400; reasons are stored and immutably recorded in the cryptographic audit trail.
- **DashboardService**: Real-time aggregation directly against PostgreSQL/SQLite with zero hardcoded metrics.
  - KPI cards: total applications, active in-flight, critical SLA breaches, compliance health, and document expiry countdowns.
  - Interactive Recharts visualizations: Route breakdown pie chart, pipeline stage distribution bar chart, and regional workload allocation.
- **ReportsService**: Granular stage age calculations and responsibility classification (`INSTITUTION` vs `AICTE_INTERNAL`). Direct CSV export with strict record-level scoping.
- **Frontend Pages**: Complete UI implementations in `frontend/src/pages/EVCManagementPage.tsx`, `frontend/src/pages/DashboardPage.tsx`, and `frontend/src/pages/ReportsPage.tsx`.

| `pytest backend/tests/test_attention_engine.py backend/tests/test_bottlenecks.py` | Test Attention Engine scoring, 5-question summary, and bottleneck triage | Exit 0 (4 passed in 5.12s) |
| `pytest` | Run complete test suite (Milestone 7) | Exit 0 (37 passed in 35.36s) |
| `npm run build --prefix frontend` | Compile production frontend bundle (Milestone 7) | Exit 0 (Success, 15.50s) |

---

## 5. Milestone 6 Completed: EVC Management & Real-Time Operational Dashboard (P1)
- **EVCService**: Physical campus inspection lifecycle: visit scheduling, confirmed dates, expert roster assignment (`EVCExpert`), and signed report submission with SHA-256 integrity verification.
- **Mandatory Delay Logging**: Rescheduling strictly rejects empty or whitespace justifications with HTTP 400; reasons are stored and immutably recorded in the cryptographic audit trail.
- **DashboardService**: Real-time aggregation directly against PostgreSQL/SQLite with zero hardcoded metrics.
  - KPI cards: total applications, active in-flight, critical SLA breaches, compliance health, and document expiry countdowns.
  - Interactive Recharts visualizations: Route breakdown pie chart, pipeline stage distribution bar chart, and regional workload allocation.
- **ReportsService**: Granular stage age calculations and responsibility classification (`INSTITUTION` vs `AICTE_INTERNAL`). Direct CSV export with strict record-level scoping.
- **Frontend Pages**: Complete UI implementations in `frontend/src/pages/EVCManagementPage.tsx`, `frontend/src/pages/DashboardPage.tsx`, and `frontend/src/pages/ReportsPage.tsx`.

---

## 6. Milestone 7 Completed: Core Innovation Engines (P1 & P2 Depth)
- **Explainable Attention Engine (Innovation A)**:
  - Deterministic multi-factor scoring formula combining SLA urgency/breach (40%), chronic deficiency returns (20%), overdue compliance undertakings (20%), expired deeds/NOCs (15%), unscheduled EVC visits (15%), and unassigned case officers (10%).
  - Transparent diagnostic explanations with individual factor points breakdown.
  - Prescriptive recommended actions and responsible RBAC role identification.
  - 5-Question structured case summary answering the core operational questions.
- **Bottleneck & Exception Cockpit (Innovation C)**:
  - Automated triage separating stalled items into "Waiting on Institution" vs "Waiting on AICTE Internal".
  - Age in state, threshold breach countdown, holding party, and next permissible bypass action.
- **Compliance Dependency Navigator (P2)**:
  - Full relational graph connecting Institution &rarr; Applications &rarr; Conditions Precedent &rarr; Prescribed Deeds.
- **Workflow Rules Interactive Browser**:
  - Full regulatory guide for Routes A, B, C, D with APH Chapter references and statutory invariants (`INV-01`, `INV-02`, `INV-03`).
- **Frontend Pages**: Complete UI implementations in `frontend/src/pages/AttentionQueuePage.tsx`, `frontend/src/pages/BottleneckCockpitPage.tsx`, `frontend/src/pages/WorkflowRulesPage.tsx`, and `frontend/src/pages/ComplianceDependenciesPage.tsx`.

---

## 7. Known Defects & Limitations
- Final end-to-end demo scripts, backup-restore automation, accessibility verification, and SIH presentation artifacts are scheduled for Milestone 8.

---

## 8. Next Steps
- Execute Milestone 8: End-to-End Validation, Demo Script, Accessibility Verification, and Final Packaging.

