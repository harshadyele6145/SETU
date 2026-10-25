# Smart India Hackathon 2026 — Problem Statement SIH26262

## Verification Status and Official Record

- **Problem Statement ID:** SIH26262
- **Title:** Integrated AICTE Approval Workflow Automation, Compliance Monitoring and Alert Management System
- **Organization:** All India Council for Technical Education (AICTE)
- **Category:** Software
- **Theme:** Smart Automation
- **Portal Reference:** https://www.sih.gov.in/sih2026PS
- **Verification Summary:** Verified via official SIH 2026 published problem statement indices and college listings. The title, theme, category, and organization match the working specification verbatim. The detailed background and functional description from the working specification (preserved in `docs/problem-statement-working-spec.md`) serve as the authoritative functional requirements baseline for SETU.

---

## Official Statement Scope Summary

### 1. Context & Purpose
AICTE oversees technical education institutions across India. Annual approvals, new institute setup, change of intake, approval extensions, time-bound undertakings, and document validity (such as registered land/lease deeds) require close monitoring across Regional Offices and central AICTE bureaus.

### 2. Core Functional Pillars
1. **Approval Workflow Automation:** Structured multi-stage routing (Only Scrutiny, Scrutiny + EVC, EVC + SAC/SHC, Only EVC), automated state transitions, deficiency returns with mandatory reasons, and resubmission tracking.
2. **Integrated Dashboard & Pendency Monitoring:** Regional and bureau-level real-time visibility, stage ageing, bottleneck detection, and immutable digital audit trail.
3. **EVC Scheduling & Alerts:** Eligibility queues, appointment coordination, schedule tracking, reminder generation, and overdue escalation.
4. **Time-Bound Undertakings & Institutional Compliance:** Digital compliance registry, condition tracking, evidence submission, two-step verification (submission does NOT equal verification), and deficiency escalation.
5. **Lease & Document Validity Monitoring:** Validity period tracking, proactive expiry warnings (e.g. 90/60/30 days), replacement submission, version linkage, and overdue enforcement.
6. **Automated Notifications, Escalations & Reports:** Idempotent alert engine, multi-channel simulated notifications, recovery after downtime, and comprehensive auditability.

### 3. Non-Negotiable Regulatory Safeguard
The system operates strictly within AICTE Approval Process Handbook (APH) norms. Automated alerts, recommendations, and prioritization engines support administrative velocity but **never replace statutory human scrutiny, physical/hybrid inspections, or decisions reserved for the Competent Authority**.

