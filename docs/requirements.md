# SETU — System Requirements Specification (SRS)

## 1. Functional Requirements Matrix

### Priority 0: Mandatory Foundation

- **REQ-F01 (Authentication & Access Control):**
  - Implement secure password hashing (bcrypt/Argon2) and JWT bearer session tokens.
  - Role-based access control supporting 8 roles: `INST_ADMIN`, `RO_OFFICER`, `BO_OFFICER`, `EVC_COORD`, `COMM_MEMBER`, `COMP_REVIEW`, `COMP_AUTH`, `SYS_ADMIN`.
  - Backend-enforced scoping: Institution isolation for `INST_ADMIN`, Regional boundary isolation for `RO_OFFICER` and regional coordinators.

- **REQ-F02 (Multi-Route Workflow Engine):**
  - Configurable state machine supporting Routes A (Only Scrutiny), B (Scrutiny + EVC), C (EVC + SAC/SHC), and D (Only EVC).
  - Validated transitions, role guards, prerequisite checks, deficiency returns with mandatory reasons, and clarification resubmissions.
  - Complete chronological timeline tracking with actor, previous state, new state, and duration in stage.

- **REQ-F03 (Compliance & Undertakings Registry):**
  - Digital tracking of conditional approval obligations with source rule, condition description, issue date, and due date.
  - Institution evidence upload with strict distinction: Uploaded evidence enters `SUBMITTED`, never automatically `VERIFIED`.
  - Reviewer verification lifecycle: `SUBMITTED` → `UNDER_VERIFICATION` → `VERIFIED` or `DEFICIENT` with mandatory review notes.

- **REQ-F04 (Document Validity & Lease Renewal):**
  - Document registry tracking categories (e.g. Registered Land Deed, Building Safety Certificate, Fire NOC, AICTE Undertaking).
  - Tracks issue date, expiry date, version number, protected local storage reference, file size, MIME type, and SHA-256 checksum.
  - Renewal submission workflow linking new versions to old versions; old expired documents remain in history.

- **REQ-F05 (Pendency, Deadlines & Alert Generation):**
  - Timezone-aware deadline calculation (`Asia/Kolkata`) with configurable calendar/business day logic.
  - Idempotent alert generation (reminder windows: 30, 15, 7, 1 day prior, and overdue).
  - Background scheduler running deadline evaluation, alert deduplication, retry tracking, and downtime recovery.

- **REQ-F06 (Audit Trail & Cryptographic Hash-Chaining):**
  - Append-only transactional audit logging for all significant events.
  - Cryptographic SHA-256 hash chaining over canonical serialized event payload and previous event hash.
  - Verification endpoint and CLI command that validates chain integrity and flags tampered events.

---

### Priority 1: Operational Demonstration & Core Innovations

- **REQ-F07 (Real-Time Dashboards & Analytics):**
  - Role-scoped summary dashboards: Active applications, pending vs. overdue counts, stage-wise distribution, regional workload.
  - Zero hardcoding: All metrics computed dynamically from persisted database state.
  - Authorized CSV export enforcing the exact same data-scoping rules.

- **REQ-F08 (EVC Operations Management):**
  - Queue for applications requiring EVC.
  - Visit scheduling with proposed and confirmed dates, roster assignments, and reschedule logs with reasons.
  - Visit completion marking, report upload tracking, and overdue reminders for pending inspection reports.

- **REQ-F09 (Explainable Attention Engine - Innovation A):**
  - Deterministic multi-factor attention scoring based on time-to-deadline, overdue duration, missing required evidence, unscheduled EVC, unassigned officer, and pending returns.
  - Transparent human-readable explanation breaking down every point contribution, supporting dates, responsible role, and recommended next action.

- **REQ-F10 (Bottleneck & Exception Cockpit - Innovation C):**
  - Automated exception detection separating "Waiting on Institution" (e.g. clarification requested, deficient evidence) from "Waiting on AICTE Internal" (e.g. unassigned scrutiny, overdue EVC report, decision pending).
  - Granular breakdown of blocked days, escalation stage, and actionable bypass/resolution options.

---

### Priority 2: Advanced Depth & Extensibility

- **REQ-F11 (Compliance Dependency Traceability - Innovation B):**
  - Direct end-to-end navigational linkage: Application → Approval Condition → Undertaking → Required Document → Deadline → Alert → Evidence Submission → Verification → Final Closure.

- **REQ-F12 (Explainable Case Summarizer - Innovation D):**
  - Deterministic structured summary synthesizing case status, chronological highlights, pending obligations, and next statutory steps without external LLM dependencies.

- **REQ-F13 (External Portal Integration Adapter):**
  - `ExternalPortalAdapter` interface with a robust, repeatable `MockPortalAdapter` demonstrating simulated successes and handled failures.

---

## 2. Non-Functional Requirements

- **REQ-NF01 (Security & Privacy):** Strong password hashing, token expiration, OWASP top 10 prevention, no sensitive data leakage in logs.
- **REQ-NF02 (Data Integrity):** Relational integrity, foreign keys, database transactions, optimistic/pessimistic concurrency guards on workflow updates.
- **REQ-NF03 (Performance):** Dashboard and queue response times under 500ms on standard local workloads.
- **REQ-NF04 (Accessibility):** WCAG 2.1 AA / GIGW compliance, keyboard navigability, high-contrast indicators, accessible ARIA roles.
- **REQ-NF05 (Observability & Health):** Health check endpoints (`/health`, `/ready`) reporting DB connectivity and scheduler status.
- **REQ-NF06 (Maintainability):** Clean separation of concerns (API routers, business services, database repositories, schema models).

