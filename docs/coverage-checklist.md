# SETU — Master Prompt Coverage Checklist

## Part 0 — Protocol & Scope Control
- [x] Preserved problem statement working spec and checked official SIH portal
- [x] Initial documentation created (research, rules, requirements, traceability, coverage)
- [x] Milestone 1 Foundation completed and verified
- [x] P0 Foundation implementation and automated tests
- [x] P0 Mandatory end-to-end gate verified
- [x] P1 Operational demonstration & core innovations (Attention Engine, Bottleneck Cockpit)
- [x] P2 Innovations (Dependency View, Case Summary, Adapter)
- [x] Demo-day fallback script (`docs/demo-script.md`) and recording checklist (`docs/demo-recording-checklist.md`)

## Part 1 — Project Identity
- [x] System name: SETU (AICTE Approval Operations Platform)
- [x] Problem Statement ID: SIH26262
- [x] Theme: Smart Automation
- [x] Persistent demo banner specified: "DEMO ENVIRONMENT — FICTIONAL DATA — NOT CONNECTED TO AICTE SYSTEMS"
- [x] 5 core operational questions addressed

## Part 2 — Research & External Adapter
- [x] `docs/current-state-research.md` created with verified sources
- [x] `docs/regulatory-rules-register.md` created with source classifications
- [x] `docs/integration-plan.md` created
- [x] `ExternalPortalAdapter` interface & `MockPortalAdapter` implemented
- [x] `backend/app/api/integrations.py` & `frontend/src/pages/IntegrationMonitorPage.tsx` operational with outage simulation

## Part 3 — Technical Stack
- [x] Frontend: React + TypeScript + Vite + Tailwind CSS + Lucide + Recharts
- [x] Backend: FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic + Pytest
- [x] Database: PostgreSQL schema + SQLite local engine + UUIDs + timezone-aware timestamps
- [x] Scheduler: Lightweight background worker for deadline evaluation & alert generation
- [x] Storage abstraction: Protected local storage, SHA-256 checksums, size and type validation
- [x] Dockerfiles & docker-compose.yml

## Part 4 — Engineering Rules
- [x] Real frontend-to-backend functionality (no static mocks)
- [x] Authoritative data persisted in database
- [x] Backend-enforced authentication and record-level permissions
- [x] Dynamic dashboard metrics (zero hardcoded counts)
- [x] Evidence submission distinct from verification (INV-01)
- [x] Cryptographic audit trail with SHA-256 hash chaining implemented & verified
- [x] Automated tests executed (48 tests passing across 14 test modules)

## Part 5 — Navigation & Design
- [x] All 15 functional navigation items implemented with role-filtered sidebar
- [x] Role-specific dashboards (Institution Action Center, Regional Scrutiny Queue, EVC Coordinator Hub, Committee Inspections, Compliance Review, Competent Authority Council Queue, Bureau Oversight)
- [x] Navy & teal government-enterprise design
- [x] WCAG 2.1 AA / GIGW 3.0 accessibility verification report (`docs/accessibility-report.md`)

## Parts 6 to 12 — Core Modules (P0)
- [x] 8 RBAC roles implemented & tested (`UserAdminPage.tsx` + 1-click persona switcher)
- [x] Strict server-side scoping and multi-tenant data isolation (with missing scope safety returning 0 records)
- [x] Routes A, B, C, D workflow state machine
- [x] Deadline calculations & timezone handling (`Asia/Kolkata`)
- [x] EVC Management (queues, scheduling, completion, report tracking)
- [x] Compliance & undertakings lifecycle
- [x] Document registry, lease validity, renewal & version history
- [x] Alert service, multi-channel simulation, idempotency, downtime recovery

## Part 13 — Innovations (P1 & P2)
- [x] Explainable Attention Engine (deterministic multi-factor scoring)
- [x] Bottleneck & Exception Cockpit (isolating AICTE vs. Institution delays)
- [x] Compliance Dependency View (full relationship navigation)
- [x] Explainable Case Summarizer (5-question operational briefing)

## Parts 14 to 20 — Data, Quality & Security
- [x] Deterministic synthetic seed data (10 institutions, 26 applications, 13 obligations, 10 documents, 35 alerts)
- [x] One-command reset-and-seed script (`python backend/seed/reset_and_seed.py`)
- [x] Pytest suite covering auth, scopes, transitions, deadlines, alerts, hash-chain, backup-restore, integrations, role dashboards & isolation (48 passed)
- [x] Local backup and restore script tested (`backend/storage/backup_restore.py` & `docs/backup-restore.md`)
- [x] Security test results and documentation (`docs/security-test-results.md`)
- [x] Electronic records retention runbook (`docs/records-and-retention.md`)
- [x] Production hardening architecture (`docs/production-hardening.md`)

