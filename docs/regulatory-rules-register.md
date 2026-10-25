# SETU — Regulatory Rules Register & Decision Matrix

## 1. Regulatory Authority & Scope Hierarchy

| Role Code | Role Name | Permitted Scope | Statutory Powers |
|---|---|---|---|
| `INST_ADMIN` | Institution Administrator | Own Institution Only | Submit application, upload evidence, submit renewal, reply to clarifications. CANNOT verify or decide. |
| `RO_OFFICER` | Regional Officer | Assigned Region | Scrutiny review, assignment, return with reason, EVC routing recommendation. |
| `BO_OFFICER` | Bureau Officer | Assigned Bureau / National | Queue oversight, inter-regional coordination, committee assignment. |
| `EVC_COORD` | EVC Coordinator | Assigned Region / Bureau | Schedule EVC dates, assign expert roster, track report submission, mark delays. |
| `COMM_MEMBER`| Committee Member | Assigned Cases Only | Record scrutiny/hearing observations, submit inspection findings. |
| `COMP_REVIEW` | Compliance Reviewer | Assigned Cases / Region | Verify uploaded compliance evidence, reject with deficiencies. Cannot grant statutory approval. |
| `COMP_AUTH` | Competent Authority | Jurisdiction Wide | Final statutory Approval / Rejection decisions based on committee recommendations. |
| `SYS_ADMIN` | System Administrator | System-wide configuration | Manage users, configure rules, monitor integrations. **No statutory decision authority.** |

---

## 2. Configured Workflow Rules & Timelines

*Note: In accordance with Part 2 and Part 8, these timelines represent Prototype Defaults calibrated for demonstration and evaluation, clearly distinguishable from statutory minimums.*

| Rule ID | Workflow Stage | Target Duration | Prototype Reminder Windows | Escalation Trigger | Classification |
|---|---|---|---|---|---|
| `RULE-SCR-01` | Initial Scrutiny | 14 Calendar Days | 7 days, 3 days, 1 day prior | Day 15 (Overdue to Regional Officer) | **PROTOTYPE DEFAULT** |
| `RULE-RESCR-02`| Re-Scrutiny Clarification | 10 Calendar Days | 5 days, 2 days prior | Day 11 (Overdue to Institution) | **PROTOTYPE DEFAULT** |
| `RULE-EVC-01` | EVC Scheduling | 14 Calendar Days | 7 days, 2 days prior | Day 15 (Escalate to Bureau Head) | **PROTOTYPE DEFAULT** |
| `RULE-EVC-02` | EVC Report Submission | 3 Calendar Days | 1 day prior, Day of visit | Day 4 (Escalate to EVC Coordinator) | **PROTOTYPE DEFAULT** |
| `RULE-SHC-01` | Standing Hearing Session | 14 Calendar Days | 7 days, 3 days prior | Day 15 (Escalate to Committee Chair) | **PROTOTYPE DEFAULT** |
| `RULE-SAC-01` | Standing Appellate Review | 21 Calendar Days | 10 days, 3 days prior | Day 22 (Escalate to Competent Authority) | **PROTOTYPE DEFAULT** |
| `RULE-DEC-01` | Final Competent Decision | 7 Calendar Days | 3 days, 1 day prior | Day 8 (Alert to Council Secretariat) | **PROTOTYPE DEFAULT** |
| `RULE-DOC-EXP` | Lease / Document Expiry | Configured Expiry Date | 90 days, 60 days, 30 days, 7 days prior | Expiry Date (Flag as Deficient/Expired) | **PROTOTYPE DEFAULT** |
| `RULE-COMP-01` | Undertaking Compliance | Configured Condition Date| 30 days, 15 days, 7 days prior | Due Date + 1 Day (Flag Overdue) | **PROTOTYPE DEFAULT** |

---

## 3. Mandatory Transition Guards & Invariants

1. **Evidence Distinct from Verification (`INV-01`):** An institution's document or evidence upload triggers the state `SUBMITTED`. It NEVER automatically transitions to `VERIFIED`. An authorized reviewer must review and record an explicit `VERIFIED` or `DEFICIENT` decision.
2. **Deficiency Return Integrity (`INV-02`):** Returning an application for clarification or deficiency requires a non-empty, audited rationale. Reversion history and previous timestamps are preserved.
3. **Statutory Decisional Boundary (`INV-03`):** Automated algorithms (including the Attention Engine and Bottleneck Cockpit) provide operational prioritisation and decision support only. Statutory approvals/rejections can only be executed by authenticated users possessing the `COMP_AUTH` role.
4. **Scope Isolation (`INV-04`):** An Institution Administrator cannot query or view records belonging to any other institution. A Regional Officer cannot perform operational actions on applications outside their assigned geographic Region.
5. **Immutable Audit Trail (`INV-05`):** Every significant workflow, compliance, document, or assignment change produces an immutable audit record linked via SHA-256 hash chaining to detect tampering.
