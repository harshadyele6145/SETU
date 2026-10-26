# SETU — Automated Testing & Quality Assurance Matrix

This document provides the complete testing strategy, test catalog, execution instructions, and benchmark targets for SETU.

---

## 1. Test Suite Summary

The SETU test suite encompasses **82 automated pytest tests** covering end-to-end approval workflows, role authorization matrices, statutory invariants, cryptographic audit trails, deadline calculation, and data provenance providers:

| Test File | Tests | Focus Area |
|---|:---:|---|
| `backend/tests/test_alerts.py` | 4 | SLA breach detection, urgent alerts, outbox delivery retries |
| `backend/tests/test_attention_engine.py` | 2 | Explainable attention scoring algorithm and diagnostic factors |
| `backend/tests/test_audit_hashchain.py` | 2 | SHA-256 sequential cryptographic hash integrity and tamper detection |
| `backend/tests/test_auth.py` | 5 | JWT token generation, password hashing, and user profile verification |
| `backend/tests/test_authorization_matrix.py` | 8 | All 9 RBAC roles, canonical aliases, statutory invariants (INV-01/02/03), fail-closed safety |
| `backend/tests/test_backup_restore.py` | 2 | Disaster recovery, snapshot creation, and database restore |
| `backend/tests/test_bottlenecks.py` | 2 | Delay attribution (AICTE vs Institution), dependency graphs |
| `backend/tests/test_compliance.py` | 3 | Undertaking lifecycle, Two-Step Evidence Gate (INV-01), cure loops |
| `backend/tests/test_dashboard.py` | 2 | Pendency aggregations, zero hardcoding, scoped CSV streaming |
| `backend/tests/test_data_integrations.py` | 7 | Public ONOD provider, duplicate prevention, malformed rejection, read-only boundary, live probe |
| `backend/tests/test_deadlines.py` | 3 | Holiday-aware business day arithmetic, IST timezone handling |
| `backend/tests/test_documents.py` | 2 | Prescribed document registry, expiry detection, protected downloads |
| `backend/tests/test_evc.py` | 2 | EVC scheduling, Route B/D eligibility, mandatory delay reasons |
| `backend/tests/test_extraction.py` | 1 | Document metadata extraction simulation |
| `backend/tests/test_health.py` | 2 | Liveness, readiness, and system health status probes |
| `backend/tests/test_integrations_and_users.py` | 2 | External adapter simulation, failure toggles, and user management |
| `backend/tests/test_p0_mandatory_gate.py` | 1 | Comprehensive end-to-end statutory gate across all 8 personas |
| `backend/tests/test_provenance_and_providers.py` | 8 | Provenance schema, Category A/B/C tagging, scheduler job ledger, X-Request-ID |
| `backend/tests/test_role_dashboards_and_isolation.py` | 6 | Object-level data isolation across all canonical RBAC roles |
| `backend/tests/test_security_boundaries.py` | 6 | Cross-tenant rejection, unauthorized transitions, missing scope safety |
| `backend/tests/test_security_scopes.py` | 3 | Server-enforced boundary validation |
| `backend/tests/test_stage_pipeline_distribution.py` | 5 | Stage pipeline aggregation, zero records handling, multi-role scoping |
| `backend/tests/test_workflow.py` | 4 | Routes A-D state machines, INV-02 deficiency return rules, resubmission |
| **TOTAL** | **82** | **100% Pass Rate** |

---

## 2. Execution Commands

### 2.1 Run Complete Backend Test Suite
```powershell
backend\venv\Scripts\pytest.exe backend\tests -v
```

### 2.2 Run Scalability & Resilience Benchmark Suite
```powershell
backend\venv\Scripts\python.exe backend\tests\benchmark_scalability.py
```

### 2.3 Run Frontend Production Build & TypeScript Typecheck
```powershell
npm --prefix frontend run build
```

---

## 3. Scalability Benchmark Results (Measured on Windows 11 AMD64, Python 3.12.10, SQLite 3.49.1)

The benchmark harness strictly distinguishes in-memory algorithms, dedicated disk-backed SQLite operations (1,000 synthetic applications), and PostgreSQL liveness:

| Category | Benchmark Task | p50 (ms) | p95 (ms) | p99 (ms) | Throughput | Target Evaluation |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **1. In-Memory Algorithm** | SLA Business-Day Engine (5,000 runs) | 0.01 | 0.02 | 0.04 | 105,027 ops/s | **PASS** (< 0.1ms p95) |
| **1. In-Memory Algorithm** | Cryptographic SHA-256 Hashing (2,000 blocks) | 0.00 | 0.00 | 0.00 | 688,539 ops/s | **PASS** (< 0.05ms p95) |
| **2. Database Layer (Disk)** | 1,000 Applications Ingestion (100-batch commits) | 22.73 | 27.27 | 27.27 | 4,480 rows/s | **PASS** (< 1500ms total) |
| **2. Database Layer (Disk)** | Indexed Filter & Paginated Scan (50 runs) | 1.83 | 4.28 | 5.54 | 506 qps | **PASS** (< 15ms p95) |
| **2. Database Layer (Disk)** | Pipeline Stage Group-By Aggregation (50 runs) | 0.96 | 2.59 | 5.87 | 780 qps | **PASS** (< 20ms p95) |
| **2. Database Layer (Disk)** | Attention Engine Multi-Factor Scoring (800 active apps) | 1,417.4 | 1,417.4 | 1,417.4 | 564 apps/s | **PASS** (< 2000ms batch) |
| **2. Database Layer (Disk)** | Audit Chain Verification (1,000 SHA-256 blocks) | 16.69 | 16.69 | 16.69 | 59,906 blocks/s | **PASS** (< 50ms total) |
| **2. Database Layer (Disk)** | Concurrent Read Threads (5 workers, 100 queries) | 16.67 | 22.44 | 27.92 | 301 req/s | **PASS** (< 25ms p95) |
| **3. PostgreSQL Engine** | PostgreSQL 16 Service Liveness Probe | 1.50 | 1.50 | 1.50 | N/A | **ONLINE (Port 5432)** |
| **4. Resilience & Recovery** | Simulated Gateway 503/504 Outage & Recovery | 0.50 | 0.50 | 0.50 | Immediate | **PASS** (Zero corrupt writes) |
| **4. Resilience & Recovery** | Missed Background Job Startup Recovery | 2.10 | 2.10 | 2.10 | 2 jobs caught up | **PASS** (Idempotent Catch-up) |

