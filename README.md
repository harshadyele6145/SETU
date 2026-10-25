# SETU — AICTE Approval Operations Platform
**SIH26262: Integrated AICTE Approval Workflow Automation, Compliance Monitoring and Alert Management System**

> **DEMO ENVIRONMENT — FICTIONAL DATA — NOT CONNECTED TO AICTE SYSTEMS.**

---

## 1. Executive Summary

SETU is an integrated, secure, and configurable government-enterprise platform purpose-built for the All India Council for Technical Education (AICTE) under Smart India Hackathon 2026 problem statement **SIH26262**.

SETU directly addresses the five core operational questions:
1. **Which applications and compliance obligations need attention now?** (Explainable Attention Engine with transparent multi-factor scoring)
2. **Why are they pending or at risk of becoming overdue?** (Bottleneck & Exception Cockpit isolating institution-side vs. AICTE-side delays)
3. **Who is responsible for the next action?** (Clear role assignments across 8 role boundaries)
4. **What must happen next, and by when?** (Stage SLAs, response clocks, and deadline windows)
5. **Can every significant action be traced?** (Append-only audit trail with SHA-256 cryptographic hash-chain verification)

---

## 2. Architecture & Technology Stack

- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS (Navy & Teal enterprise theme), Lucide Icons, Recharts.
- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic migrations, Pytest.
- **Database:** PostgreSQL (production / Docker Compose) and SQLite (cross-compatible zero-configuration local execution).
- **Security:** Bcrypt password hashing, signed JWT bearer sessions, institution and regional scope enforcement.
- **Auditability:** Cryptographic SHA-256 hash chaining over serialized events with tamper detection.
- **Background Worker:** Non-blocking scheduler for idempotent deadline tracking and downtime catch-up.

---

## 3. Local Setup & Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- (Optional) Docker and Docker Compose

### Step 1: Clone and Configure Environment
```bash
git clone <repo-url>
cd SETU
cp .env.example .env
```

### Step 2: Backend Setup
```bash
# Set up Python virtual environment
python -m venv backend/venv

# Activate virtual environment (Windows PowerShell)
.\backend\venv\Scripts\Activate.ps1
# On Linux/macOS: source backend/venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run database migrations
alembic upgrade head

# Run backend automated tests
pytest
```

### Step 3: Frontend Setup
```bash
cd frontend
npm install
npm run build
```

### Step 4: Run Locally
- **Backend API:**
  ```bash
  uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
  ```
  API Documentation: http://127.0.0.1:8000/api/docs
  Health Check: http://127.0.0.1:8000/health

- **Frontend Portal:**
  ```bash
  cd frontend
  npm run dev
  ```
  Portal URL: http://localhost:5173

---

## 4. Docker Deployment
```bash
docker-compose up --build
```
This boots up PostgreSQL 15, runs Alembic migrations, seeds synthetic data, and serves the frontend on port 5173 / 80.

---

## 5. Documentation Sitemap

- [Problem Statement (Working Spec)](docs/problem-statement-working-spec.md)
- [Official Problem Statement](docs/problem-statement.md)
- [System Requirements Specification](docs/requirements.md)
- [Requirements Traceability Matrix](docs/requirements-traceability.md)
- [Current State Domain Research](docs/current-state-research.md)
- [Regulatory Rules & Scope Register](docs/regulatory-rules-register.md)
- [System Architecture](docs/architecture.md)
- [Relational Data Model](docs/data-model.md)
- [Workflow Rules & State Machine](docs/workflow-rules.md)
- [External Integration Plan](docs/integration-plan.md)
- [Engineering Progress Ledger](docs/progress.md)
- [Coverage Checklist](docs/coverage-checklist.md)
