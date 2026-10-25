# SETU — Master Prompt Coverage Checklist

## Part 0 — Protocol & Scope Control
- [x] Preserved problem statement working spec and checked official SIH portal
- [x] Initial documentation created (research, rules, requirements, traceability, coverage)
- [x] Milestone 1 Foundation completed and verified
- [ ] P0 Foundation implementation and automated tests
- [ ] P0 Mandatory end-to-end gate verified
- [ ] P1 Operational demonstration & core innovations (Attention Engine, Bottleneck Cockpit)
- [ ] P2 Innovations (Dependency View, Case Summary, Adapter)
- [ ] Demo-day fallback script (`docs/demo-script.md`) and recording checklist

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

## Part 3 — Technical Stack
- [x] Frontend: React + TypeScript + Vite + Tailwind CSS + Lucide + Recharts
- [x] Backend: FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic + Pytest
- [x] Database: PostgreSQL schema + SQLite local engine + UUIDs + timezone-aware timestamps
- [ ] Scheduler: Lightweight background worker for deadline evaluation & alert generation
- [x] Storage abstraction: Protected local storage, SHA-256 checksums, size and type validation
- [x] Dockerfiles & docker-compose.yml

## Part 4 — Engineering Rules
- [x] Real frontend-to-backend functionality (no static mocks)
- [x] Authoritative data persisted in database
- [ ] Backend-enforced authentication and record-level permissions
- [ ] Dynamic dashboard metrics (zero hardcoded counts)
- [ ] Evidence submission distinct from verification
- [x] Cryptographic audit trail with SHA-256 hash chaining implemented
- [x] Automated tests executed

## Part 5 — Navigation & Design
- [x] All 15 functional navigation items implemented
- [x] Navy & teal government-enterprise design
- [ ] WCAG 2.1 AA / GIGW accessibility considerations

## Parts 6 to 12 — Core Modules (P0)
- [ ] 8 RBAC roles implemented & tested
- [ ] Routes A, B, C, D workflow state machine
- [ ] Deadline calculations & timezone handling (`Asia/Kolkata`)
- [ ] EVC Management (queues, scheduling, completion, report tracking)
- [ ] Compliance & undertakings lifecycle
- [ ] Document registry, lease validity, renewal & version history
- [ ] Alert service, multi-channel simulation, idempotency, downtime recovery

## Part 13 — Innovations (P1 & P2)
- [ ] Explainable Attention Engine (deterministic multi-factor scoring)
- [ ] Bottleneck & Exception Cockpit (isolating AICTE vs. Institution delays)
- [ ] Compliance Dependency View (full relationship navigation)
- [ ] Explainable Case Summarizer

## Parts 14 to 20 — Data, Quality & Security
- [ ] Deterministic synthetic seed data (10+ institutions, 25+ applications, 12+ obligations)
- [ ] One-command reset-and-seed script
- [ ] Pytest suite covering auth, scopes, transitions, deadlines, alerts, and hash-chain
- [ ] Local backup and restore script tested
- [ ] Security test results and documentation
