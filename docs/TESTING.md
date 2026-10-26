# SETU — Automated Testing & Quality Assurance Matrix

This document provides the complete testing strategy, test catalog, execution instructions, and benchmark targets for SETU.

---

## 1. Test Suite Summary

The SETU test suite encompasses **62 automated pytest tests** covering end-to-end approval workflows, RBAC multi-tenant isolation, cryptographic audit trails, deadline calculation, and data provenance providers:

| Test File | Tests | Focus Area |
|---|:---:|---|
| `backend/tests/test_alerts.py` | 4 | SLA breach detection, urgent alerts, outbox delivery retries |
| `backend/tests/test_attention_engine.py` | 2 | Explainable attention scoring algorithm and diagnostic factors |
| `backend/tests/test_audit_hashchain.py` | 2 | SHA-256 sequential cryptographic hash integrity and tamper detection |
| `backend/tests/test_auth.py` | 5 | JWT token generation, password hashing, and user profile verification |
| `backend/tests/test_backup_restore.py` | 2 | Disaster recovery, snapshot creation, and database restore |
| `backend/tests/test_bottlenecks.py` | 2 | Delay attribution (AICTE vs Institution), dependency graphs |
| `backend/tests/test_compliance.py` | 3 | Undertaking lifecycle, Two-Step Evidence Gate (INV-01), cure loops |
| `backend/tests/test_dashboard.py` | 2 | Pendency aggregations, zero hardcoding, scoped CSV streaming |
| `backend/tests/test_deadlines.py` | 3 | Holiday-aware business day arithmetic, IST timezone handling |
| `backend/tests/test_documents.py` | 2 | Prescribed document registry, expiry detection, protected downloads |
| `backend/tests/test_evc.py` | 2 | EVC scheduling, Route B/D eligibility, mandatory delay reasons |
| `backend/tests/test_extraction.py` | 1 | Document metadata extraction simulation |
| `backend/tests/test_health.py` | 2 | Liveness, readiness, and system health status probes |
| `backend/tests/test_integrations_and_users.py` | 2 | External adapter simulation, failure toggles, and user management |
| `backend/tests/test_p0_mandatory_gate.py` | 1 | Comprehensive end-to-end statutory gate across all 8 personas |
| `backend/tests/test_provenance_and_providers.py` | 8 | Provenance schema, Category A/B/C tagging, scheduler job ledger, X-Request-ID |
| `backend/tests/test_role_dashboards_and_isolation.py` | 6 | Object-level data isolation across all 8 canonical RBAC roles |
| `backend/tests/test_security_boundaries.py` | 6 | Cross-tenant rejection, unauthorized transitions, missing scope safety |
| `backend/tests/test_security_scopes.py` | 3 | Server-enforced boundary validation |
| `backend/tests/test_workflow.py` | 4 | Routes A-D state machines, INV-02 deficiency return rules, resubmission |
| **TOTAL** | **62** | **100% Pass Rate** |

---

## 2. Execution Commands

### 2.1 Run Complete Backend Test Suite
```bash
pytest backend/tests
```

### 2.2 Run Scalability Benchmark Suite
```bash
python backend/tests/benchmark_scalability.py
```

### 2.3 Run Frontend Production Build & TypeScript Typecheck
```bash
npm --prefix frontend run build
```

---

## 3. Scalability Benchmark Results

Executed against simulated high-volume datasets:

| Benchmark Scenario | Dataset Size | Measured Latency | Measured Throughput | Target SLA | Status |
|---|:---:|:---:|:---:|:---:|:---:|
| Bulk Application Ingestion | 1,000 records | 48.89 ms | 20,452 ops/sec | < 1,000 ms | **PASS** |
| Scoped & Filtered Query Scan | 1,000 records | 4.45 ms | 225 queries/sec | < 50 ms | **PASS** |
| Attention Engine Batch Scoring | 1,000 records | 932.15 ms | 0.932 ms/app | < 2.0 ms/app | **PASS** |
| SHA-256 Audit Chain Verification | 1,000 blocks | 12.06 ms | 82,948 blocks/sec | < 50 ms | **PASS** |
| Statutory Business-Day Calculator | 5,000 cycles | 34.38 ms | 145,453 calcs/sec | < 100 ms | **PASS** |
