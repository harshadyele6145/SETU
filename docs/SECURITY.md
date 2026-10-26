# SETU — Enterprise Security Architecture & Zero-Trust Governance

This document details the security posture, authentication protocols, role-based access control (RBAC), cryptographic audit guarantees, and statutory privacy compliance for SETU.

---

## 1. Zero-Trust Access Control & 8-Role RBAC

SETU enforces fine-grained authorization at both the API route and database query level:

| Role Code | Role Name | Permitted Scope | Scoping Enforcement Key |
|---|---|---|---|
| `INST_ADMIN` | Institution Admin | Single assigned institution | `user.institution_id` |
| `RO_OFFICER` | Regional Officer | Single assigned administrative region | `user.region_id` |
| `REGIONAL_DIR` | Regional Director | Single assigned administrative region | `user.region_id` |
| `EVC_COORD` | EVC Coordinator | Single assigned administrative region | `user.region_id` |
| `COMM_MEMBER` / `COMMITTEE_MBR` | Committee Member | Assigned inspection visits only | EVC Roster email match |
| `COMP_REV` / `COMP_REVIEW` | Compliance Reviewer | Regional compliance queue | `user.region_id` |
| `BO_OFFICER` / `BUREAU_OFFICER` | Bureau Officer | Pan-India operational oversight | None (National level) |
| `SYS_ADMIN` | System Administrator | Platform configuration & security | Pan-India administrative |

### Missing Scope Safety Gate
If an authenticated user lacks an expected scoping attribute (e.g. `user.institution_id == None` for `INST_ADMIN`), the server defaults to returning **0 records** (`[]` or HTTP 403), never falling back to an unconstrained dataset.

---

## 2. Cryptographic Append-Only Audit Ledger (SHA-256)

Every critical action (submission, scrutiny return, officer reassignment, EVC reschedule, evidence review) is committed to an immutable cryptographic hash chain in `backend/app/models/audit.py`:

```
+-----------------------------------------------------------------------------------------+
|                               CRYPTOGRAPHIC AUDIT CHAIN                                 |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|  [Genesis Block: seq=0]                                                                 |
|  current_hash = "0000000000000000000000000000000000000000000000000000000000000000"    |
|       ^                                                                                 |
|       | previous_hash                                                                   |
|  [Event 1: seq=1, action=APPLICATION_SUBMITTED]                                         |
|  current_hash = SHA256(seq=1 | timestamp | actor | action | entity | previous_hash)     |
|       ^                                                                                 |
|       | previous_hash                                                                   |
|  [Event 2: seq=2, action=DEFICIENCY_RETURN]                                             |
|  current_hash = SHA256(seq=2 | timestamp | actor | action | entity | previous_hash)     |
|                                                                                         |
+-----------------------------------------------------------------------------------------+
```

Any modification, deletion, or out-of-sequence insertion of historical records invalidates the downstream SHA-256 hash sequence, immediately detected by `audit_service.verify_integrity()`.

---

## 3. Defense-in-Depth HTTP Security Headers

Implemented via `backend/app/middleware/observability.py`, every HTTP response includes:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
X-Permitted-Cross-Domain-Policies: none
X-Request-ID: req_<correlation_id>
```

---

## 4. Statutory Compliance with DPDP Act, 2023

1. **Explicit Data Classification**: Clear partitioning between Synthetic Seed (Category A), Public Reference (Category B), and Real Operational Records (Category C).
2. **Access Limitation**: Zero cross-institution data leakage; institutional administrators cannot inspect peer institutions.
3. **Auditability**: Complete actor identity, role, and client IP recorded on every statutory determination.
4. **No Telemetry PII**: Sensitive contact credentials (phone numbers, personal emails) are masked or omitted in public telemetry feeds.

