# SETU (SIH26262) — Official Demonstration Script & Jury Runbook

**System Name:** SETU (AICTE Approval Operations Platform)  
**Problem Statement:** SIH26262 — Smart Automation  
**Demo Safety Banner:** `DEMO ENVIRONMENT — FICTIONAL DATA — NOT CONNECTED TO AICTE SYSTEMS`  
**Universal Demo Password:** `DemoPass@2026`  

---

## Executive Demonstration Overview

This script provides an exact, step-by-step walkthrough covering 9 comprehensive demonstration scenarios (Demos A through I). Each scenario highlights a critical regulatory requirement, operational innovation, or statutory invariant implemented in SETU.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DEMO FLOW ARCHITECTURE                          │
├───────────────────┬───────────────────────────────┬────────────────────┤
│ Phase 1: Ingestion│ Phase 2: Scrutiny & Field Ev. │ Phase 3: Statutory │
│ • App Submission  │ • Deficiency Return (INV-02)  │ • Two-Step (INV-01)│
│ • SLA Deadlines   │ • Expert Committee (EVC)      │ • Council (INV-03) │
├───────────────────┼───────────────────────────────┼────────────────────┤
│ Phase 4: Intel.   │ Phase 5: Resilience & Outbox  │ Phase 6: Scoping   │
│ • Attention Engine│ • Outbox Downtime Catchup     │ • 8 RBAC Roles     │
│ • Bottleneck Cock.│ • Cryptographic Hash Auditing │ • Adapter Sandbox  │
└───────────────────┴───────────────────────────────┴────────────────────┘
```

---

## Pre-Demonstration Reset (1 Command)

Before starting the evaluation, execute the repeatable reset script to prime the database with pristine synthetic institutions, applications, and logs:
```bash
python backend/seed/reset_and_seed.py
```
*Expected Terminal Output:*
`[SUCCESS] SETU database seeded with 26 applications, 10 institutions, 13 obligations, 10 documents, 35 alerts, and 10 user personas.`

---

## Demo A: Mandatory P0 Workflow & Scrutiny Engine

**Objective:** Demonstrate compliant application submission, SLA deadline assignment, and server-enforced regional scoping.

1. **Sign In as Institution Administrator:**
   - URL: `http://localhost:5173/`
   - Email: `inst_admin@fictional-nist.edu.in` | Password: `DemoPass@2026`
   - Notice the institution banner: *National Institute of Science & Tech (North)*.
2. **Navigate to Applications (`/applications`):**
   - Click **"New Application"**.
   - Select **Academic Year:** `2026-2027`.
   - Select **Application Type:** `Extension of Approval (EoA)`.
   - Select **Workflow Route:** `ROUTE_A (Standard EoA)`.
   - Click **"Create Application"**. Status starts in `DRAFT`.
3. **Submit Application:**
   - Click **"Submit Application"** on the newly created record.
   - Status transitions to `SUBMITTED`. The Scrutiny SLA clock begins.
4. **Switch Persona to Regional Office Officer:**
   - Navigate to `/users` -> Demo Persona Switcher -> Click **"Switch Persona"** for **Shri Amitabh Sharma** (`ro_north@aicte.gov.in`).
5. **Verify Regional Scoping Boundary:**
   - Open `/applications`.
   - Observe that Northern Region applications are visible, but Southern/Western regional queues are omitted.
   - Click into the submitted application.
   - Click **"Begin Scrutiny"**. Status advances to `UNDER_SCRUTINY`.

---

## Demo B: Deficiency Return & Clarification Loop (Invariant INV-02)

**Objective:** Prove that returns cannot be arbitrary; they require mandatory deficiency reasons and automatically increment the `return_count`.

1. **Attempt Empty Return (Defensive UX Check):**
   - As `ro_north@aicte.gov.in`, open an application in `UNDER_SCRUTINY`.
   - Attempt to click return without deficiency reasons. The system blocks submission and prompts for itemized deficiency text.
2. **Submit Compliant Deficiency Return:**
   - Enter Deficiency Reason: `"Deficiency in Clause 4.2: Land ownership title deed missing municipal occupancy certificate for Block C."`
   - Click **"Return with Deficiencies"**.
   - Notice: Application status changes to `DEFICIENCY_COMMUNICATED`, `return_count` increments from `0` to `1`.
3. **Switch Persona back to Institution:**
   - Go to `/users` -> Switch to `inst_admin@fictional-nist.edu.in`.
   - Open `/applications`. The returned application visibly highlights the deficiency notice and `DEFICIENCY_COMMUNICATED` state.
4. **Submit Resubmission with Clarification:**
   - Click **"Resubmit with Clarifications"**.
   - Enter: `"Uploaded certified municipal occupancy certificate dated 14-Oct-2026 for Block C."`
   - Status transitions to `RESUBMITTED`. Audit log appends clarification timestamp.

---

## Demo C: Condition Precedent Undertakings & Two-Step Verification (Invariant INV-01)

**Objective:** Validate Invariant INV-01: uploaded proof enters `SUBMITTED`, never automatically `VERIFIED`. Compliance reviewer must accept or reject.

1. **Institution Views Obligations (`/compliance`):**
   - Sign in as `inst_admin@fictional-nist.edu.in`.
   - Open the **Compliance Undertakings** module.
   - Locate pending condition precedent (e.g. *Fire Safety System Modernization*).
   - Click **"Upload Evidence"**. Enter reference number `NOC-FIRE-2026-991` and upload PDF document.
   - **Crucial Invariant Check:** Status becomes `SUBMITTED`. The badge shows **"PENDING REGULATORY REVIEW"**. It is NOT verified!
2. **Reviewer Validates Evidence:**
   - Switch Persona to **Compliance Reviewer** (`compliance_reviewer@aicte.gov.in`).
   - Open `/compliance`. Filter by `SUBMITTED`.
   - Click **"Accept & Mark Verified"**.
   - Status changes to `VERIFIED`. Verification timestamp and reviewer user ID are permanently recorded in the cryptographic audit trail.

---

## Demo D: Document Expiry, Lease Renewal & Automatic Warning

**Objective:** Show the centralized Document Validity Registry tracking 30-day and 60-day expiry windows.

1. **Navigate to Documents (`/documents`):**
   - Sign in as `inst_admin@fictional-nist.edu.in` or `ro_north@aicte.gov.in`.
   - Observe documents color-coded by validity:
     - **Green:** Valid (> 60 days).
     - **Amber:** Expiring Soon (15 to 45 days remaining).
     - **Red:** Expired or Invalidation Imminent.
2. **Register a Document Renewal:**
   - Select an expiring lease document.
   - Click **"Register Renewal"**.
   - Provide new validity date: `2030-12-31`.
   - Upload new registration deed.
   - System updates validity status to `VALID` and creates a linked audit record.

---

## Demo E: Multi-Tier Deadline Intelligence & Downtime Recovery

**Objective:** Demonstrate compound idempotency keys (`f"{entity_type}:{entity_id}:{alert_type}:{window_day}"`) and outbox catchup after downtime.

1. **Navigate to Alerts (`/alerts`):**
   - Observe alerts categorized by severity: `T-60`, `T-30`, `T-15`, `T-7`, and `OVERDUE`.
   - Note the compound idempotency keys in the details modal preventing dual alert creation.
2. **Navigate to Notification Outbox Recovery (`/notifications-recovery`):**
   - View pending, delivered, and dead-letter outbox items.
   - Highlight:
     - Exponential backoff retry counter (`retry_count / max_retries`).
     - Safe idempotency key on each transactional dispatch.
     - Click **"Trigger Downtime Catch-Up"** to execute the background catch-up worker live.

---

## Demo F: Expert Visit Committee (EVC) Inspection Lifecycle

**Objective:** Demonstrate committee scheduling from the accredited expert roster, mandatory delay justifications, and report uploads.

1. **Switch Persona to EVC Coordinator:**
   - Switch to **Prof. Arvind Kulkarni** (`evc_coord@aicte.gov.in`).
   - Open `/evc`.
2. **Schedule Inspection:**
   - Click **"Schedule Committee Visit"**.
   - Select Application in `EVC_SCHEDULED` queue.
   - Assign 3 experts from the panel roster.
   - Select inspection date.
3. **Simulate Reschedule with Mandatory Justification:**
   - Click **"Reschedule Visit"**.
   - Attempt to reschedule without a reason: blocked by backend validation.
   - Enter reason: `"Severe monsoon flooding in district; physical campus inaccessible."`
   - System records the reschedule with mandatory audit note.
4. **Submit Visit Report:**
   - Upload signed EVC report PDF.
   - Status transitions to `EVC_COMPLETED`.

---

## Demo G: Sole Statutory Authority Council Decision (Invariant INV-03)

**Objective:** Prove Invariant INV-03: neither RO Officers nor EVC members can approve an application. Only `COMP_AUTH` has legal authority.

1. **Attempt Approval as RO Officer:**
   - Switch to `ro_north@aicte.gov.in`.
   - Open an application. Note that the **"Final Approval"** and **"Statutory Rejection"** buttons are absent or return 403 Forbidden on API call.
2. **Switch to Competent Authority (`comp_auth@aicte.gov.in`):**
   - Open `/applications`.
   - Click into the scrutinised application.
   - Observe Council Decision controls unlocked:
     - **Grant Statutory Approval (EoA)**
     - **Grant Conditional Approval**
     - **Statutory Rejection**
   - Enter Council Meeting Minute Reference: `AICTE/EC/2026/112/MIN-04`.
   - Click **"Grant Statutory Approval"**.
   - Notice: Application status updates to `APPROVED`. Official approval reference generated.

---

## Demo H: Explainable Attention Priority Queue & Bottleneck Cockpit

**Objective:** Answer the 5 operational questions: *What needs attention now? Why? Who is responsible? What happens next? Can it be traced?*

1. **Open Explainable Attention Engine (`/attention`):**
   - View composite urgency score (0-100) combining:
     - Deadline proximity weight (40%)
     - Historical deficiency count (20%)
     - Compliance gap severity (25%)
     - EVC pending days (15%)
   - Click on any case card to expand the **"Why This Case Needs Attention"** explainability breakdown.
2. **Open Bottleneck & Exception Cockpit (`/bottlenecks`):**
   - View systemic pendency metrics across 4 stages: Scrutiny, EVC, Compliance, and Council.
   - Inspect the **"Root Cause Pendency Breakdown"** identifying whether delays stem from institutional inaction or council backlog.
3. **Open Compliance Dependencies Navigator (`/dependencies`):**
   - View interactive dependency tree showing which condition-precedent undertakings block final approval.

---

## Demo I: External Portal Integration & Outage Resilience

**Objective:** Demonstrate the `ExternalPortalAdapter` boundary and graceful failure handling.

1. **Navigate to AICTE Integration Monitor (`/integration`):**
   - Observe Gateway Status: `ONLINE & CONNECTED`.
2. **Execute Live Push Decision:**
   - Under *Simulate Outbound Decision Push*, enter Application No and click **"Execute Outbound Push Decision"**.
   - Observe live telemetry row generated: `200 OK`, `AICTE-SYNC-<timestamp>`.
3. **Simulate Gateway Outage:**
   - Click **"Simulate 503/504 Outage"**.
   - Gateway status turns red: `SIMULATED OUTAGE ACTIVE`.
   - Execute push test again: system gracefully logs `504 FAIL (Simulated Gateway Timeout)` and queues event in transactional outbox for automated recovery.
4. **Restore Gateway:**
   - Click **"Disable Failure Simulation"**. Gateway returns to healthy state.
