# SETU — Reliability, Scalability & Real-Time Data Integration Audit

**Date:** 2026-10-26  
**Auditor:** Senior Full-Stack & Systems Architecture Review Team  
**Evaluation Target:** SETU (Statutory Evaluation & Tracking Unit) — AICTE Approval Operations Platform (SIH26262)

---

## 1. Executive Summary & Baseline Results

SETU is currently a functioning, demonstrable approval operations platform designed around the AICTE Approval Process Handbook (APH 2024–27). It implements a FastAPI Python backend, a React 18 TypeScript frontend, SQLite (with PostgreSQL schema support), role-scoped dashboards, and deterministic statutory workflow rules.

### Baseline Verification Results (Phase 0)
- **Backend Test Suite**: `54 passed in 43.29s` across 15 test modules (`pytest -v backend/tests`).
- **Frontend Production Build**: `Exit Code 0` in 10.13s (2304 modules transformed, 0 TypeScript/ESLint errors).
- **Git Tree**: Clean working tree on branch `main`.

---

## 2. Current Architecture & System Topology

| Tier | Current Implementation | Planned Production Target |
|---|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Recharts | Production static assets served via NGINX / Cloud CDN |
| **Backend API** | FastAPI 0.162.0, Pydantic v2, Uvicorn ASGI | Multi-worker Uvicorn / Gunicorn with structured logging |
| **Database** | SQLite 3 (`setu.db`) via SQLAlchemy 2.0 | PostgreSQL 16 with connection pooling (`pool_pre_ping`, `pool_size=20`) |
| **Migrations** | Alembic migration framework (`alembic/`) | Versioned Alembic migrations applied before startup |
| **Security/Auth** | JWT (`HS256`), bcrypt password hashing, 8 RBAC roles | Rotating RSA keys (`RS256`), rate-limiting, hardened security headers |
| **Scheduler** | APScheduler BackgroundScheduler (in-memory) | Persistent job execution ledger with distributed lock safety |
| **Audit Ledger** | Sequential SHA-256 hash-chained `AuditEvent` table | Immutable database triggers / HSM / KMS signed blocks |

---

## 3. Existing Architectural Strengths

1. **Strict Statutory Workflow Finite State Machine**:
   - Accurately models Routes A, B, C, and D per APH 2024–27.
   - Restricts final statutory approval and rejection decisions solely to the Competent Authority (`COMP_AUTH` / Invariant INV-03).
   - Enforces mandatory itemized deficiency reasoning before returning an application (`INV-02`).
2. **Two-Step Compliance Verification (`INV-01`)**:
   - Institutional evidence uploads are quarantined in `SUBMITTED` state until verified by an authorized officer.
3. **Multi-Tenant Scoping & Fail-Safe Security**:
   - Scopes queries by institution, region, and committee assignment; safely returns 0 records when user scope is missing.
4. **Sequential Cryptographic Audit Trail**:
   - Every mutation is hash-chained with `previous_hash` &rarr; `current_hash`, enabling instant tamper detection.
5. **Case Accountability & Handoff Diagnostics**:
   - Real-time holding responsibility (`WAITING_ON_INSTITUTION` vs `WAITING_ON_AICTE`), statutory SLA countdown, and candidate action permissibility checks.

---

## 4. Confirmed Defects, Gaps, and Production Risks

### A. Data Provenance & Trust Boundary Defect
- **Issue**: Database tables (`institutions`, `applications`) lack explicit provenance fields (`source_system`, `external_id`, `is_synthetic`, `sync_status`, `synced_at`).
- **Risk**: In a pilot or production setting, synthetic demonstration data could be confused with genuine public reference data or operational records.
- **Remediation**: Add a standardized provenance mixin and Alembic migration to tag all records with authoritative origins.

### B. Single-Threaded In-Memory Scheduler
- **Issue**: Background alerts and deadline evaluations run on an in-memory timer without persistent run logs in the database.
- **Risk**: If the server restarts or scales to multiple worker instances, duplicate jobs or missed alert windows may occur without an administrative audit trail.
- **Remediation**: Create a persistent `JobExecution` database model to record job execution history, execution duration, and outcomes.

### C. Missing Structured Observability & Correlation IDs
- **Issue**: FastAPI request logs lack unified correlation IDs (`X-Request-ID`) across concurrent user requests.
- **Risk**: Troubleshooting concurrent operations, slow database queries, or integration timeouts is difficult in multi-user deployments.
- **Remediation**: Add ASGI middleware to assign/propagate `X-Request-ID` and structured JSON logs.

### D. External Integration Provider Framework
- **Issue**: External portal adapter is currently hardcoded as a single mock class (`MockPortalAdapter`).
- **Risk**: No clean architectural boundary exists to connect real public reference datasets (e.g. AICTE Open Data / ONOD) alongside test mocks.
- **Remediation**: Build a multi-provider integration registry supporting:
  1. `MockPortalProvider` (for testing/simulations).
  2. `AICTEOpenDataProvider` (for official public institutional reference data).
  3. Bounded retries, exponential backoff, rate-limiting, and payload signature verification.

### E. PostgreSQL Deployment Hardening
- **Issue**: Current configuration defaults to SQLite with local file locks.
- **Risk**: Concurrency bottlenecks when multiple officers perform simultaneous scrutiny or batch approvals.
- **Remediation**: Provide complete Docker Compose configuration with PostgreSQL 16, connection pooling parameters, `.env.example`, and migration scripts.

---

## 5. Data Sources Classification

| Category | Description | Storage Strategy | Provenance Tag |
|---|---|---|---|
| **Category A: Synthetic Data** | Seeded institutions, sample dossiers, artificial lease deeds, demo users | Kept isolated for development & automated tests | `source_system="SYNTHETIC_SEED"`, `is_synthetic=True` |
| **Category B: Public Reference Data** | AICTE public institutional directory, approved programmes, district/state codes, ONOD portal | Imported via verified public provider, cached with freshness TTL | `source_system="AICTE_ONOD_PUBLIC"`, `is_synthetic=False` |
| **Category C: Real Operational Data** | Live institutional applications, scrutiny remarks, EVC inspections, council approval orders | Authorized internal users only, permanent audit chain | `source_system="SETU_OPERATIONAL"`, `is_synthetic=False` |

---

## 6. Audit Trail Limitations & Protections

- **Cryptographic Guarantees**: The SHA-256 hash chain mathematically guarantees that *if* an event exists in the chain, it cannot be modified, deleted, or reordered without invalidating all subsequent block hashes.
- **Known Limitations**:
  - A hash chain does not guarantee that an event was originally recorded if a rogue system bypasses the audit service entirely.
  - A privileged database superuser (`postgres` root) with direct write access could hypothetically recompute an entire chain from a given point.
- **Mitigations**:
  - Wrap all critical mutations in transactional units (`db.commit()` only after `record_event()`).
  - Anchor the Genesis Hash and maintain an external ledger checkpoint in production.
