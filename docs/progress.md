# SETU — Engineering Progress & Milestone Tracking

## Session Date: 2026-10-25
**Branch:** `master`  
**Completed Milestones:**
- Milestone 1 — Foundation
- Milestone 2 — Authentication and Data Model (P0)

---

## 1. Work Completed in Milestone 2
- Implemented core authentication system using bcrypt password hashing and signed JWT bearer tokens.
- Defined 8 official RBAC roles: `INST_ADMIN`, `RO_OFFICER`, `BO_OFFICER`, `EVC_COORD`, `COMM_MEMBER`, `COMP_REVIEW`, `COMP_AUTH`, and `SYS_ADMIN`.
- Built server-enforced scoping functions:
  - `enforce_institution_scope`: strictly limits Institution Admins to their assigned institution.
  - `enforce_region_scope`: strictly confines Regional Officers to their designated geographic region.
  - `require_statutory_authority`: enforces regulatory boundary reserving statutory approvals/rejections to Competent Authority (`COMP_AUTH`).
- Implemented API endpoints in `backend/app/api/auth.py`:
  - `POST /api/auth/login`
  - `POST /api/auth/logout`
  - `GET /api/auth/me`
- Implemented synthetic database seeding script (`backend/seed/seed_data.py`):
  - 5 Regions (North, West, South, East, Central)
  - 10 Fictional Technical Institutions
  - 10 Demo Users across all 8 roles with default credential `DemoPass@2026`
  - 4 Workflow Routes (Routes A, B, C, D) and 36 Workflow Stages
  - Genesis cryptographic audit event
- Built frontend `AuthContext` and integrated interactive persona switcher in the navigation header.
- Authored and verified comprehensive automated tests in `test_auth.py` and `test_security_scopes.py`.

---

## 2. Commands Executed & Results
| Command | Purpose | Result / Exit Code |
|---|---|---|
| `python -m backend.seed.seed_data` | Seed database with synthetic institutions & users | Exit 0 (Success) |
| `pytest backend/tests/test_auth.py backend/tests/test_security_scopes.py` | Run auth & scope tests | Exit 0 (8 passed in 2.20s) |
| `pytest` | Run full test suite | Exit 0 (10 passed in 4.02s) |
| `npm run build --prefix frontend` | Verify frontend compilation with auth context | Exit 0 (Success, 11.91s) |

---

## 3. Known Defects & Limitations
- All demo user passwords are set to `DemoPass@2026` for prototype evaluation; production deployment requires mandatory credential change and MFA integration.

---

## 4. Next Steps
- Execute Milestone 3: Implement multi-route Workflow Engine (Routes A, B, C, D), transition guards, mandatory return reasons, application timelines, and cryptographic audit hash-chain verification.
