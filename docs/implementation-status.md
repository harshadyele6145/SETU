# SETU — Implementation Status & Verification Ledger

| Module / Subsystem | Target Milestone | Current Status | Supporting Evidence / Artifact |
|---|---|---|---|
| Project Scaffolding & Health API | Milestone 1 | VERIFIED & DONE | `backend/app/main.py`, `backend/app/api/health.py`, tests pass |
| Problem Statement & Research Docs | Milestone 1 | VERIFIED & DONE | `docs/problem-statement.md`, `docs/current-state-research.md` |
| Regulatory Rules & Scope Matrix | Milestone 1 | VERIFIED & DONE | `docs/regulatory-rules-register.md` |
| Relational Data Model & Migrations | Milestone 1 | VERIFIED & DONE | `backend/alembic/versions/*_initial_schema.py` |
| Frontend Shell & 15 Nav Views | Milestone 1 | VERIFIED & DONE | `frontend/src/App.tsx`, `frontend/src/components/Sidebar.tsx` |
| External Portal Adapter Interface | Milestone 1 | IMPLEMENTED | `backend/app/adapters/external_portal.py` |
| Authentication & RBAC (8 Roles) | Milestone 2 | VERIFIED & DONE | `backend/app/api/auth.py`, `backend/tests/test_auth.py` (5 passed) |
| Scope-Enforced Data Isolation | Milestone 2 | VERIFIED & DONE | `backend/app/services/auth_service.py`, `backend/tests/test_security_scopes.py` (3 passed) |
| Workflow State Machine (4 Routes) | Milestone 3 | VERIFIED & DONE | `backend/app/services/workflow_engine.py`, `backend/tests/test_workflow.py` (4 passed) |
| Audit Trail & SHA-256 Hash Chaining | Milestone 3 | VERIFIED & DONE | `backend/app/services/audit_service.py`, `backend/tests/test_audit_hashchain.py` (2 passed) |
| Reset & Seed Script (26 Synthetic Apps)| Milestone 3 | VERIFIED & DONE | `backend/seed/reset_and_seed.py` |
| Applications & Timeline UI Pages | Milestone 3 | VERIFIED & DONE | `frontend/src/pages/ApplicationsPage.tsx`, `frontend/src/pages/TimelinePage.tsx` |
| Compliance Obligations & Evidence | Milestone 4 | VERIFIED & DONE | `backend/app/services/compliance_service.py`, `backend/tests/test_compliance.py` (3 passed) |
| Document Registry & Expiry Tracking | Milestone 4 | VERIFIED & DONE | `backend/app/services/document_service.py`, `backend/tests/test_documents.py` (2 passed) |
| Deadline Evaluator & Alerts Engine | Milestone 5 | VERIFIED & DONE | `backend/app/services/deadline_service.py`, `backend/app/services/alert_service.py`, `backend/tests/test_alerts.py` (7 passed) |
| EVC Management & Report Tracking | Milestone 6 | VERIFIED & DONE | `backend/app/services/evc_service.py`, `backend/tests/test_evc.py` (2 passed) |
| Live Dashboard & Reporting | Milestone 6 | VERIFIED & DONE | `backend/app/services/dashboard_service.py`, `backend/app/api/reports.py`, `backend/tests/test_dashboard.py` (2 passed) |
| Explainable Attention Engine (P1) | Milestone 7 | PLANNED | Scoring algorithm designed |
| Bottleneck & Exception Cockpit (P1) | Milestone 7 | PLANNED | Classifier designed |
| End-to-End Validation & Fallback Script | Milestone 8 | PLANNED | Script outline planned |

*Legend: PLANNED -> IN PROGRESS -> IMPLEMENTED -> TESTED -> VERIFIED & DONE*

