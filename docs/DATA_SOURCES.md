# SETU — Data Provenance & Source Classification Register

This document establishes the definitive data provenance taxonomy, classification boundaries, and audit traceability standards for SETU (SIH26262), ensuring full transparency and statutory integrity during institutional evaluation and pilot rollout.

---

## 1. Statutory Data Classification Framework

To uphold governmental credibility and comply with the **Digital Personal Data Protection (DPDP) Act, 2023**, SETU enforces a strict three-tier classification architecture across all institutional profiles, application workflows, and compliance records:

```
+-----------------------------------------------------------------------------------------+
|                                SETU DATA TAXONOMY                                       |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|  [CATEGORY A: SYNTHETIC DATA]                                                           |
|  * Source System: "SYNTHETIC_SEED"                                                      |
|  * Flag: is_synthetic = True                                                            |
|  * Purpose: Demonstration of edge-case approval lifecycles, SLA breach meters,          |
|    deficiency loops, and stress testing without touching actual live records.           |
|                                                                                         |
|  [CATEGORY B: PUBLIC REFERENCE DATA]                                                    |
|  * Source System: "AICTE_ONOD_PUBLIC"                                                   |
|  * Flag: is_synthetic = False                                                           |
|  * Purpose: Ingestion of verified public institutional directories, approved programs,  |
|    NIRF ranking benchmarks, and intake quotas published on the official AICTE Portal.   |
|                                                                                         |
|  [CATEGORY C: REAL OPERATIONAL DATA]                                                    |
|  * Source System: "SETU_OPERATIONAL"                                                    |
|  * Flag: is_synthetic = False                                                           |
|  * Purpose: Directly authenticated submissions, EVC expert inspection uploads,          |
|    and compliance evidence cryptographically verified in production.                    |
|                                                                                         |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Field-Level Provenance Mapping

Every persistent model inheriting `DataProvenanceMixin` tracks the following audit metadata:

| Attribute | SQL Type | Nullable | Default | Description |
|---|---|:---:|---|---|
| `source_system` | `VARCHAR(50)` | No | `'SETU_OPERATIONAL'` | Origin system identifier (`SYNTHETIC_SEED`, `AICTE_ONOD_PUBLIC`, `SETU_OPERATIONAL`) |
| `external_id` | `VARCHAR(100)` | Yes | `NULL` | External primary key or national registry index (e.g., AICTE Permanent ID) |
| `source_record_version` | `VARCHAR(50)` | Yes | `NULL` | Version or snapshot identifier from the upstream catalog (e.g., `ONOD-2026.01`) |
| `source_updated_at` | `TIMESTAMP` | Yes | `NULL` | Wall-clock timestamp of when the upstream authoritative record was last revised |
| `synced_at` | `TIMESTAMP` | No | `CURRENT_TIMESTAMP` | Timestamp when SETU synchronized and validated the local mirror |
| `sync_status` | `VARCHAR(50)` | No | `'SYNCED'` | Operational sync status (`SYNCED`, `PENDING_RETRY`, `FAILED`, `SUPERSEDED`) |
| `is_synthetic` | `BOOLEAN` | No | `FALSE` | Explicit statutory disclosure flag; `TRUE` permanently disables production certification |
| `last_sync_error` | `TEXT` | Yes | `NULL` | Diagnostic error payload captured if synchronization encountered schema discrepancies |

---

## 3. Public Reference Datasets (Category B)

SETU includes an adapter for official AICTE Open Data Portal / ONOD (Open Network for Official Datasets):

| Entity / Dataset | Upstream Source | Update Frequency | SETU Consumption Mode |
|---|---|---|---|
| **Approved Technical Institutions Directory** | `https://onod.aicte-india.org/` | Annual / Periodic Gazette | Tested upstream probe; offline snapshot fallback `ONOD-2026.01` |
| **Approved Programme & Intake Catalog** | AICTE National Portal | Per Approval Cycle | Read-only reference lookup during Route A-D validation |
| **State / District / Pin Jurisdiction Matrix** | Department of Higher Education (MoE) | Static / Annual Gazette | Regional mapping across Northern, Western, Southern, Eastern, Central ROs |
| **Gazetted National Holidays List** | DoPT / Ministry of Personnel | Annual | Calendar engine input for statutory working-day SLA reckoning |

### 3.1 Upstream ONOD Live Probe & Gateway Diagnostics

On October 27, 2026, an automated network probe was executed against the official national ONOD gateway:
- **Target URL**: `https://onod.aicte-india.org/`
- **Gateway Server**: `Microsoft-Azure-Application-Gateway/v2`
- **Probe HTTP Status**: `502 Bad Gateway`
- **Diagnostic Finding**: The public gateway endpoint is either in maintenance or restricted to private VNet / NIC intranet peering. Public automated unauthenticated REST querying is blocked upstream.
- **Statutory Integrity Compliance**: SETU does **not** fabricate simulated live responses or claim a live operational connection to AICTE production backends. The provider explicitly reports `is_connected = False` and surfaces a clear warning in the Integration Monitor while serving the verified gazetted reference catalog snapshot (`ONOD-2026.01`).

---

## 4. Synthetic Seed Data Guarantees (Category A)

To protect institutional reputations and prevent confusion:
1. **Fictional Names**: All seeded institutions bear the explicit suffix `"(Fictional)"` or fictional institute names (e.g., `National Institute of Science & Technology (Fictional)`).
2. **Dedicated ID Ranges**: Synthetic Permanent IDs use reserved prefixes (`1-1002345xx`).
3. **UI Trust Badges**: The user interface renders an amber `[SYNTHETIC]` badge across all application lists, case timelines, and institutional profiles.
4. **Zero Live Gateway Mutations**: The `MockPortalProvider` operates entirely in-memory and never executes external HTTP/mTLS requests to government hostnames.

---

## 5. Transition to Production Operational Data (Category C)

When deploying for an authorized institutional pilot:
1. Initialize the database using `alembic upgrade head` without executing `seed_data.py`.
2. Connect to the state or central identity provider (Jan Parichay / MeriPehchaan) via SAML 2.0 or OpenID Connect.
3. Configure `BaseIntegrationProvider` with approved NIC client certificates (`mTLS`) and Council API keys.
4. All inbound applications created through institutional portals will default to:
   - `source_system = "SETU_OPERATIONAL"`
   - `is_synthetic = False`
   - `sync_status = "SYNCED"`
   - Cryptographic SHA-256 hash chaining on all workflow determinations.

