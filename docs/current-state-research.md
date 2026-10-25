# SETU — Current State Research & AICTE Workflow Domain Analysis

## 1. Regulatory Context & Authoritative Sources

| Area | Official Source | Direct Reference / URL | Publication / Access Date | Confidence & Classification |
|---|---|---|---|---|
| AICTE Approval Process | AICTE Approval Process Handbook (APH) 2024-27 | https://www.aicte-india.org/bulletins/approval-process-handbook | 2024 / Accessed Oct 2026 | **VERIFIED** |
| SIH 2026 Problem Statement | SIH 2026 Problem Portal (SIH26262) | https://www.sih.gov.in/sih2026PS | SIH 2026 / Accessed Oct 2026 | **VERIFIED** |
| Digital Security & Records | Information Technology Act, 2000 & CERT-In Directives | https://www.cert-in.org.in | Updated 2023 / Accessed Oct 2026 | **VERIFIED** |
| Government Web Accessibility | Guidelines for Indian Government Websites (GIGW 3.0) & WCAG 2.1 AA | https://guidelines.india.gov.in | 2023 / Accessed Oct 2026 | **VERIFIED** |

---

## 2. AICTE Approval Stages & Committee Taxonomy

Based on the verified AICTE Approval Process Handbook (APH):

### A. Scrutiny Committee (SC) & Re-Scrutiny
- **Purpose:** Verification of initial digital documents, eligibility criteria, land/building registrations, institutional society bylaws, financial stability, and prerequisite compliance.
- **Workflow:** If deficiencies are observed, the application is marked as deficient with specific recorded reasons. The institution can submit clarifications/corrections for Re-Scrutiny.
- **Classification:** **VERIFIED**

### B. Expert Visit Committee (EVC)
- **Purpose:** On-site (or authorized hybrid/remote) physical inspection conducted by senior academicians and technical experts appointed by the Regional Office.
- **Focus:** Physical infrastructure, instructional area, administrative area, amenities, laboratories, workshop equipment, library volumes, computers, faculty cadres, and safety clearances (fire, structural stability).
- **Outcome:** Detailed inspection report submitted via portal with clear findings.
- **Classification:** **VERIFIED**

### C. Standing Hearing Committee (SHC)
- **Purpose:** A quasi-judicial hearing provided to an institution before adverse recommendations or rejections are finalized, giving institutional representatives the right of being heard (natural justice principle).
- **Classification:** **VERIFIED**

### D. Standing Appellate Committee (SAC)
- **Purpose:** The apex appeal committee that hears appeals from institutions against decisions such as rejection of approval or intake reduction.
- **Outcome:** Recommendation to the AICTE Executive Committee for final decision by the Competent Authority.
- **Classification:** **VERIFIED**

---

## 3. Approval Route Archetypes

Under APH provisions, different application types trigger distinct evaluation pipelines:

1. **Route A (Only Scrutiny):** For minor adjustments, continuation of standard approvals (Extension of Approval - EoA) without expansion, minor nomenclature changes.
   - *Flow:* Submission → Scrutiny Committee → Regional Recommendation → Competent Authority Decision.
2. **Route B (Scrutiny + EVC):** For new institutions, significant increase in intake, introduction of new faculties/programmes, or restoration of intake.
   - *Flow:* Submission → Scrutiny Committee → EVC Queue & Scheduling → EVC Inspection & Report → Regional Review → Decision.
3. **Route C (EVC + SAC/SHC):** When an inspection reveals critical deficiencies or an institution appeals an adverse finding.
   - *Flow:* EVC Deficiencies → SHC / SAC Hearing → Committee Observation → Final Approval / Rejection.
4. **Route D (Only EVC):** For surprise physical verification, complaint-driven inspections, or specific infrastructure audit mandates.
   - *Flow:* Mandated Inspection → EVC Scheduling → Visit & Report Submission → Competent Authority Review.

---

## 4. Institutional Compliance & Lease Validity

### Time-Bound Undertakings
- Often approvals are accorded with conditions precedent or conditions subsequent (e.g., completion of specific laboratory equipment installation, barrier-free access construction, submission of pending municipal occupancy certificate within 6 months).
- **Core Gap:** Monitoring whether institutions fulfill these undertakings before their next annual cycle without manual spreadsheet tracking.
- **Classification:** **HYPOTHESIS / VERIFIED IN PRACTICE**

### Land & Lease Document Validity
- Technical institutions operating on leased premises must hold registered lease deeds valid for a minimum statutory period (e.g., 30 years or balance validity as specified in APH).
- Lease expiry without timely renewal places institutional standing in jeopardy.
- **Classification:** **VERIFIED**

---

## 5. System Gaps & SETU Innovation Boundaries

| Feature Area | Current AICTE Baseline | SETU Solution | Classification |
|---|---|---|---|
| Workflow Automation | Static portal form submission with discrete stages | Configurable, stage-gated finite state machine with automatic queue movement | **PROTOTYPE DEFAULT** |
| Attention Prioritization | First-in-first-out or manual officer sorting | **Explainable Attention Engine** with transparent multi-factor scoring | **INNOVATION (P1)** |
| Bottleneck Detection | Retrospective statistical reporting | **Bottleneck & Exception Cockpit** isolating delay causes and holding parties | **INNOVATION (P1)** |
| Traceability & Tamper Detection | Relational database logging | Append-only audit events with cryptographic SHA-256 hash chaining | **ENGINEERING PILLAR** |
| AICTE Live Integration | Dedicated internal databases and legacy portals | Modular `ExternalPortalAdapter` with robust `MockPortalAdapter` for prototype | **INTEGRATION BOUNDARY** |
