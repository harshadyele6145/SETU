# SETU (SIH26262) — Demonstration Video Recording & Screen Capture Checklist

**Fallback Plan:** In the event of network disruption, hardware malfunction, or conference projector issues during the Smart India Hackathon jury presentation, this checklist specifies the timed video captures and high-resolution screenshots required for seamless demonstration.

---

## 1. Recording Specifications

- **Resolution:** 1920x1080 (Full HD, 1080p, 60fps)
- **Audio:** Clear voiceover explaining user persona, statutory rule, and observed result.
- **Visual Hygiene:**
  - Browser in 100% zoom (Chrome or Edge).
  - Clean dev console (no unhandled red errors).
  - Safety banner clearly visible at the top: `DEMO ENVIRONMENT — FICTIONAL DATA — NOT CONNECTED TO AICTE SYSTEMS`.

---

## 2. Timed Demonstration Video Schedule (Total: 6 Minutes)

| Segment | Time | Screen / Route | Persona | Key Regulatory & Technical Actions |
|---|---|---|---|---|
| **01: Overview & P0 Path** | 00:00 - 00:45 | `/` -> `/applications` | `inst_admin` | - Login, review operational metrics<br>- Create Route A EoA application<br>- Submit application, initiate Scrutiny SLA |
| **02: Scrutiny & Scoping** | 00:45 - 01:30 | `/users` -> `/applications` | `ro_north` | - Quick persona switch to RO North<br>- Demonstrate regional scoping (Kanpur RO cannot see Western files)<br>- Begin scrutiny on submitted application |
| **03: Deficiency Return (INV-02)** | 01:30 - 02:15 | `/applications` | `ro_north` & `inst_admin` | - Attempt return without reason (blocked by UX)<br>- Enter itemized deficiency text -> Submit return<br>- Verify `return_count` = 1<br>- Switch to `inst_admin` -> resubmit with clarification |
| **04: Two-Step Compliance (INV-01)** | 02:15 - 03:00 | `/compliance` | `inst_admin` & `comp_rev` | - Inst Admin uploads fire NOC proof<br>- **Highlight Invariant INV-01**: Enters `SUBMITTED`, not `VERIFIED`<br>- Switch to `comp_rev` -> review PDF proof -> Mark `VERIFIED` |
| **05: Document Expiry & Deadlines** | 03:00 - 03:45 | `/documents` & `/alerts` | `ro_north` | - Filter documents by expiring soon (30-day window)<br>- Demonstrate lease renewal workflow<br>- Inspect compound idempotency keys in `/alerts` |
| **06: EVC Committee Inspection** | 03:45 - 04:30 | `/evc` | `evc_coord` | - Open EVC Management page<br>- Schedule 3-member committee from expert roster<br>- Demonstrate mandatory delay justification on reschedule<br>- Upload inspection report |
| **07: Statutory Council Decision (INV-03)** | 04:30 - 05:00 | `/applications` | `comp_auth` | - Demonstrate RO Officer denied approval privilege (403 Forbidden)<br>- Switch to Council Chair (`comp_auth`)<br>- Record council minute reference -> Grant statutory Approval |
| **08: Priority Engine & Bottlenecks** | 05:00 - 05:30 | `/attention` & `/bottlenecks` | `bureau_officer` | - Inspect multi-factor urgency scoring (0-100)<br>- Expand explainability breakdown ("Why this case needs attention")<br>- Inspect stage-wise bottleneck delays |
| **09: Outage Resilience & Hash Audit** | 05:30 - 06:00 | `/integration` & `/audit` | `comp_auth` | - Trigger simulated 503 gateway outage<br>- Observe transactional outbox catchup<br>- Open `/audit` -> click "Verify Cryptographic Audit Chain" -> Show 100% hash integrity |

---

## 3. High-Resolution Screenshot Capture Checklist

Capture the following 12 PNG screenshots at 1920x1080 and store in `docs/screenshots/`:

- [ ] `01_dashboard_live_metrics.png`: Main dashboard showing dynamic SLA counters and pendency distribution.
- [ ] `02_applications_queue_scoped.png`: Applications table showing Northern Region filtered queue.
- [ ] `03_deficiency_return_modal.png`: Return modal demonstrating mandatory deficiency reason requirement.
- [ ] `04_compliance_two_step_submitted.png`: Compliance undertaking showing `SUBMITTED` state (never auto-verified).
- [ ] `05_document_registry_renewal.png`: Document registry showing 30-day expiry warning and renewal action.
- [ ] `06_alerts_compound_idempotency.png`: Alerts list showing multi-tier SLA deadlines and compound deduplication keys.
- [ ] `07_notification_outbox_recovery.png`: Outbox dashboard showing retry counts and downtime recovery trigger.
- [ ] `08_evc_management_roster.png`: EVC scheduler showing assigned experts and visit timeline.
- [ ] `09_competent_authority_approval.png`: Council decision modal reserved exclusively for `COMP_AUTH`.
- [ ] `10_attention_priority_queue.png`: Explainable Attention Engine showing multi-factor scoring.
- [ ] `11_bottleneck_exception_cockpit.png`: Bottleneck cockpit showing root cause pendency analytics.
- [ ] `12_integration_monitor_telemetry.png`: Integration monitor showing live telemetry and outage simulation toggle.
