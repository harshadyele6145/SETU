# SETU — Electronic Records Management and Regulatory Retention Policy

**Platform:** SETU (AICTE Approval Operations Platform)  
**Statutory Framework:** Information Technology Act, 2000 (Sections 4, 7, 7A) & Digital Personal Data Protection (DPDP) Act, 2023  
**Applicability:** Technical Education Institutions, Regional AICTE Offices, Council Bureaus  

---

## 1. Statutory Context and Purpose

Under Section 7 of the Information Technology Act, 2000, any document, record, or information required by law to be retained for any specified period is legally satisfied if retained in an electronic form, provided:
1. The electronic record remains accessible and usable for subsequent reference;
2. It is retained in the format in which it was originally generated, sent, or received, or in a format which can be demonstrated to represent accurately the information originally generated; and
3. The details which will facilitate the identification of the origin, destination, date, and time of dispatch or receipt of such electronic record are available in the electronic record.

SETU is architected to fully comply with these statutory requirements.

---

## 2. Retention Schedules by Record Classification

| Classification | Examples in SETU | Statutory Retention Period | Storage Architecture | Immutable Guarantee |
|---|---|:---:|---|---|
| **Statutory Council Decisions** | Final Approval Letters (EoA), Rejection Orders, Executive Committee Minutes | **Permanent (Indefinite)** | Primary PostgreSQL DB + Cold Object Storage Archive | Cryptographically chained in `audit_events`; non-deletable. |
| **Audit Ledger (`audit_events`)** | Cryptographic hash-chained events, logins, status changes, deficiency returns | **Permanent (Minimum 10 Years)** | Append-only database table; no SQL `DELETE` or `UPDATE` grants. | Sequential SHA-256 hash chaining. |
| **Regulatory Documents** | Land titles, 30-year leases, AICTE NOCs, Fire Safety Certificates | **Duration of Affiliation + 7 Years** | Protected file storage with SHA-256 checksum tracking. | Versioned with renewal histories in `document_registry`. |
| **Compliance Evidence** | Photographs, geofenced inspection proofs, financial endowments | **7 Years Post-Approval Cycle** | Protected upload directory with access logs. | Linked to condition-precedent undertakings in `compliance_obligations`. |
| **Expert Inspection Reports** | EVC Committee findings, deficiency matrices, expert signatures | **10 Years** | PDF archive with metadata verification. | Signed by expert committee members in `evc_reports`. |
| **Alert & Outbox Telemetry** | SLA deadline warnings, email/SMS dispatch receipts, recovery logs | **3 Years** | Pruned after 36 months to cold partitioned tables. | Compound idempotency keys prevent duplicates. |

---

## 3. Immutable Ledger Guarantees

1. **No Destructive Database Operations:**
   - In production database roles, the application user `setu_app` is granted `SELECT`, `INSERT`, and limited `UPDATE` permissions on operational tables.
   - The `audit_events` table is configured with `INSERT` and `SELECT` **only**. Even database administrators cannot execute `UPDATE` or `DELETE` without breaking the sequential cryptographic hash chain.
2. **Sequential Hash Chain Formula:**
   $$\text{Hash}_n = \text{SHA-256}(\text{Seq}_n \parallel \text{Timestamp}_n \parallel \text{ActorRole}_n \parallel \text{Action}_n \parallel \text{Entity}_n \parallel \text{Details}_n \parallel \text{Hash}_{n-1})$$
3. **Automated Verification:**
   - The backup and disaster recovery utility (`backend/storage/backup_restore.py`) automatically runs `audit_service.verify_chain()` on every snapshot before acknowledging successful point-in-time recovery.

---

## 4. Digital Personal Data Protection (DPDP) Act Compliance

- **Data Minimization:** Only authorized officer credentials, institutional contacts, and expert panel affiliations are stored. No Aadhaar numbers or non-essential personal identifiers are collected.
- **Purpose Limitation:** Contact details are strictly utilized for regulatory alerts, deficiency notifications, and statutory approval dispatches.
- **Sovereign Hosting:** All production database clusters and document repositories must reside exclusively on sovereign Indian infrastructure (NIC MeghRaj or MeitY-empaneled cloud service providers).
