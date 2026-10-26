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

## 7. Milestone 8 Completed: End-to-End Validation, Demo Script, and Final Packaging
- **Backup, Restore & Verification Runbook**:
  - Implemented `backend/storage/backup_restore.py` supporting online SQLite backups and enterprise PostgreSQL continuous archiving.
  - Generates SHA-256 manifests (`setu_backup_*.json`) and performs sandbox restore verification checking cryptographic audit hash chain integrity (`AuditService.verify_chain()`).
  - Automated tests in `backend/tests/test_backup_restore.py` passing 100%.
  - Authoring of `docs/backup-restore.md`.
- **External Integration Adapter Monitor**:
  - Built `backend/app/api/integrations.py` exposing health, simulated 503/504 outage toggling, push decision sync, and inbound master data fetch.
  - Implemented `frontend/src/pages/IntegrationMonitorPage.tsx` with live telemetry probe viewer, test console, and production prerequisite checklists.
  - Routed `/integration` in `frontend/src/App.tsx`.
- **User & Access Scope Administration**:
  - Built `backend/app/api/users.py` with scoped account listings and 8 RBAC role definitions.
  - Implemented `frontend/src/pages/UserAdminPage.tsx` with 1-click Demo Persona Switcher (8 roles), database users table, and statutory permission matrix.
  - Routed `/users` in `frontend/src/App.tsx`.
- **Official SIH Demonstration & Production Artifacts**:
  - `docs/demo-script.md`: Exhaustive 9-step demo guide (Demos A through I) with exact credentials, clicks, and expected results.
  - `docs/demo-recording-checklist.md`: 6-minute timed video capture guide and 12 high-resolution screenshot checklist.
  - `docs/accessibility-report.md`: WCAG 2.1 AA and GIGW 3.0 accessibility verification report.
  - `docs/security-test-results.md`: Complete audit of 41 security tests covering invariants INV-01, INV-02, INV-03, multi-tenant scoping, and cryptographic hash chains.
  - `docs/records-and-retention.md`: Electronic records retention policy compliant with IT Act 2000 (Sec 7) and DPDP Act 2023.
  - `docs/production-hardening.md`: Enterprise architecture for PostgreSQL high availability, connection pooling, non-root containers, and private object storage.

| Command Executed | Purpose | Result |
|---|---|---|
| `python backend/storage/backup_restore.py --action backup` | Test automated database backup | Exit 0 (Backup and SHA-256 manifest created) |
| `python backend/storage/backup_restore.py --action verify --file <backup>` | Test sandboxed restore and hash chain verification | Exit 0 (Verification PASSED, 100% hash chain intact) |
| `python backend/seed/reset_and_seed.py` | Reset DB and seed synthetic data | Exit 0 (26 apps, 10 insts, 35 alerts, 10 personas) |
| `pytest backend/tests/test_backup_restore.py` | Automated backup & tamper detection tests | Exit 0 (2 passed in 0.26s) |
| `pytest backend/tests/test_integrations_and_users.py` | Automated adapter & user scoping tests | Exit 0 (2 passed in 2.19s) |
| `pytest -v backend/tests` | Run complete backend automated test suite | Exit 0 (41 passed in 27.14s) |
| `npm run build --prefix frontend` | Compile production frontend bundle | Exit 0 (Success, 15.50s) |

---

## 9. Role-Specific Dashboards & Strict Multi-Tenant Data Isolation (Delivered & Verified)
- **Role-Specific Dashboard Workspaces**:
  - Implemented tailored operational action queues in `backend/app/services/dashboard_service.py` under `role_view` for all 8 roles (`INST_ADMIN`, `RO_OFFICER`, `REGIONAL_DIR`, `EVC_COORD`, `COMM_MEMBER`/`COMMITTEE_MBR`, `COMP_REVIEW`/`COMP_REV`, `BO_OFFICER`/`BUREAU_OFFICER`, `COMP_AUTH`).
  - Adapted `frontend/src/pages/DashboardPage.tsx`:
    - `INST_ADMIN`: Action Center with Deficiency Notices requiring resubmission, Pending Compliance Undertakings countdowns, Prescribed Document Expiry Reminders, and My Applications tracking table. Zero regional workload table exposure.
    - `RO_OFFICER` & `REGIONAL_DIR`: Regional Scrutiny Queue (with stage age days and return count), Deficiency Returns, SLA Deadlines, and single-region workload allocation.
    - `EVC_COORD`: Awaiting Inspection Scheduling queue and Pending Inspection Reports queue.
    - `COMM_MEMBER`: Assigned Inspection Visits and report submission tracker.
    - `COMP_REVIEW`: Evidence Awaiting Verification queue with direct verification actions.
    - `COMP_AUTH`: Council Statutory Decision Queue for SAC/SHC-recommended applications and recent council determinations.
    - `BUREAU_OFFICER`: National operational summary and 5-region cross-regional workload oversight.
- **Server-Side Data Scoping & Missing Scope Safety**:
  - Implemented strict server-side scoping and missing scope safety across `applications.py`, `reports.py`, `compliance.py`, `documents.py`, `document_service.py`, `evc_service.py`, and `alert_service.py`.
  - Added fail-safe protection: if a scoped role (`INST_ADMIN` or `RO_OFFICER`) lacks an `institution_id` or `region_id`, queries return 0 records (`false()`) rather than leaking unrestricted data.
  - Restricted committee members strictly to applications, documents, compliance undertakings, and visits where their contact email is assigned.
- **Role-Filtered Navigation**:
  - Updated `frontend/src/components/Sidebar.tsx` to conditionally render navigation items based on the authenticated user's role.
- **Automated Regression Test Suite**:
  - Authored `backend/tests/test_role_dashboards_and_isolation.py` (6 tests) verifying institution isolation, single-region scoping, cross-regional authority views, committee member assignment checks, missing scope safety, and dashboard count consistency.
  - Full suite expanded to 48 tests passing 100%.

| Command Executed | Purpose | Result |
|---|---|---|
| `pytest backend/tests/test_role_dashboards_and_isolation.py` | Role dashboard & data isolation regression tests | Exit 0 (6 passed in 4.86s) |
| `pytest -v backend/tests` | Run complete backend automated test suite | Exit 0 (48 passed in 27.55s) |
| `npm run build --prefix frontend` | Compile production frontend bundle | Exit 0 (Success, 46.38s) |

---

## 10. Judge-Impact Improvement Sprint & Case Accountability Feature (Delivered & Verified)
- **Case Accountability & Handoff View (`GET /api/applications/{id}/accountability`)**:
  - Distinctive visual banner isolating holding party: "Waiting on Institution" vs "Waiting on AICTE Internal".
  - Exact SLA countdown, stage age, deadline, and overdue badge in Indian Standard Time (IST).
  - Explicit action authority indicator: "Authorized to Execute Next Action" vs "Observer Mode (Role Restricted)".
  - Candidate permitted statutory actions for the current stage with one-click modal execution.
  - Transparent attention engine scoring factor breakdown and active statutory undertakings/blockers.
  - Direct SHA-256 cryptographic audit block link anchor.
- **Workflow & Data Isolation Hardening**:
  - Fixed Bottleneck Cockpit holding categorization: deficiency return stages (`SCRUTINY_DEFICIENT`, `DEFICIENCY_COMMUNICATED`) correctly attribute responsibility to `WAITING_ON_INSTITUTION`.
  - Added missing-scope safety and committee member assignment filtering to both `AttentionService` and `BottleneckService`.
  - Enforced server-side transition checks in `WorkflowEngine` preventing unauthorized submissions, returns, resubmissions, and officer reassignments.
- **Persona & Seeding Alignment**:
  - Expanded `seed_data.py` to seed all 14 demo accounts with canonical role names and aliases (`REGIONAL_DIR`, `BUREAU_OFFICER`, `COMMITTEE_MBR`, `COMP_REV`).
  - Seeded initial `EVCVisit` and `EVCExpert` records for Route B and Route D applications so EVC Coordinator and Committee Member personas work out-of-the-box in evaluation demos.
  - Aligned `DEMO_USERS` in `AuthContext.tsx` and removed hardcoded localhost URLs across frontend pages.
- **Automated Regression Suite Expansion**:
  - Authored `backend/tests/test_security_boundaries.py` (6 tests) covering submission security, deficiency return rules, reassignment permissions, committee member visit scoping, and accountability contracts.
  - Full automated test suite expanded to **54 passing tests** (100% pass rate).
  - Frontend production build verified (`npm run build --prefix frontend`).

| Command Executed | Purpose | Result |
|---|---|---|
| `pytest backend/tests/test_security_boundaries.py` | Security boundaries & accountability regression tests | Exit 0 (6 passed in 7.57s) |
| `pytest -q backend/tests` | Run complete backend automated test suite | Exit 0 (54 passed in 35.52s) |
| `python backend/seed/reset_and_seed.py` | Reset DB and seed synthetic data + EVC visits | Exit 0 (26 apps, 14 users, 35 alerts, hash chain verified) |
| `npm run build --prefix frontend` | Compile production frontend bundle | Exit 0 (Success, 0 errors, dist generated) |

---

## 11. Final Status and Deliverables Summary
- **Backend**: FastAPI modular architecture with 12 API routers, 11 service domains, 48 passing automated tests.
- **Frontend**: React 18, TypeScript, Tailwind CSS, Recharts, 14 production pages compiled to `dist/`.
- **Database**: PostgreSQL / SQLite with 14 relational tables, foreign key constraints, indexes, and sequential cryptographic audit hash chaining.
- **Statutory Safeguards**: Invariants INV-01, INV-02, INV-03 fully operational and tested.
- **Role Dashboards**: Full 8-role tailored dashboards and strict multi-tenant server-enforced scoping.
- **Demo Readiness**: 1-command reset script (`python backend/seed/reset_and_seed.py`), 8-role persona switcher, and comprehensive demo runbook (`docs/demo-script.md`).


