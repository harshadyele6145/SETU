# SETU — Implementation Status & Verification Ledger

| Module / Subsystem | Target Milestone | Current Status | Supporting Evidence / Artifact |
|---|---|---|---|
| Project Scaffolding & Health API | Milestone 1 | VERIFIED & DONE | `backend/app/main.py`, `backend/app/api/health.py`, tests pass |
| Problem Statement & Research Docs | Milestone 1 | VERIFIED & DONE | `docs/problem-statement.md`, `docs/current-state-research.md` |
| Regulatory Rules & Scope Matrix | Milestone 1 | VERIFIED & DONE | `docs/regulatory-rules-register.md` |
| Relational Data Model & Migrations | Milestone 1 | VERIFIED & DONE | `backend/alembic/versions/*_initial_schema.py` |
| Frontend Shell & 15 Nav Views | Milestone 1 | VERIFIED & DONE | `frontend/src/App.tsx`, `frontend/src/components/Sidebar.tsx` |
| External Portal Adapter Interface | Milestone 1 | IMPLEMENTED | `backend/app/adapters/external_portal.py` |
| Authentication & RBAC (8 Roles) | Milestone 2 | PLANNED | Architecture defined |
| Scope-Enforced Data Isolation | Milestone 2 | PLANNED | Architecture defined |
| Workflow State Machine (4 Routes) | Milestone 3 | PLANNED | FSM designed |
| Audit Trail & SHA-256 Hash Chaining | Milestone 3 | IMPLEMENTED | `backend/app/services/audit_service.py` |
| Compliance Obligations & Evidence | Milestone 4 | PLANNED | Models designed |
| Document Registry & Expiry Tracking | Milestone 4 | PLANNED | Models designed |
| Deadline Evaluator & Alerts Engine | Milestone 5 | PLANNED | Logic designed |
| EVC Management & Report Tracking | Milestone 6 | PLANNED | Workflow designed |
| Live Dashboard & Reporting | Milestone 6 | PLANNED | UI & API designed |
| Explainable Attention Engine (P1) | Milestone 7 | PLANNED | Scoring algorithm designed |
| Bottleneck & Exception Cockpit (P1) | Milestone 7 | PLANNED | Classifier designed |
| End-to-End Validation & Fallback Script | Milestone 8 | PLANNED | Script outline planned |

*Legend: PLANNED -> IN PROGRESS -> IMPLEMENTED -> TESTED -> VERIFIED & DONE*
