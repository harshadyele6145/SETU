# SETU — Enterprise Deployment, PostgreSQL Hardening & Operations Guide

This guide details the production deployment architecture, PostgreSQL connection pool configuration, container orchestration, and disaster recovery procedures for SETU.

---

## 1. Production Architecture Overview

```
                      [HTTPS / TLS 1.3 - Port 443]
                                   |
                                   v
                      +-------------------------+
                      |       Nginx / NIC       |
                      |      Reverse Proxy      |
                      +-------------------------+
                                   |
                    +--------------+--------------+
                    |                             |
                    v                             v
       +-------------------------+   +-------------------------+
       |   SETU Frontend Pod     |   |    SETU Backend Pod     |
       |     React 18 / Vite     |   |   FastAPI (ASGI) / Uvicorn
       |   (Nginx Alpine: 80)    |   |    Python 3.12 (Port 8000)  |
       +-------------------------+   +-------------------------+
                                                  |
                                                  v
                                     +-------------------------+
                                     |  PostgreSQL 16 HA Cluster|
                                     |  * Connection Pooling   |
                                     |  * Automated Failover   |
                                     |  * Persistent Volume    |
                                     +-------------------------+
```

---

## 2. PostgreSQL Connection Pooling Configuration

In `backend/app/core/database.py`, the database engine automatically detects PostgreSQL and applies production connection pooling:

| Parameter | Production Value | Purpose |
|---|:---:|---|
| `pool_size` | `20` | Base pool of persistent database connections maintained per worker. |
| `max_overflow` | `10` | Maximum surge connections permitted during traffic spikes (total 30). |
| `pool_timeout` | `30` | Seconds a worker will wait for a connection before raising an exception. |
| `pool_recycle` | `1800` | Connections recycled every 30 minutes to prevent stale TCP drops behind cloud firewalls. |
| `pool_pre_ping` | `True` | Executes a lightweight `SELECT 1` ping before handing a connection to a session, discarding dead sockets. |

---

## 3. Container Orchestration (Docker Compose)

The repository provides a production-grade `docker-compose.yml`:

```bash
# 1. Clone repository and setup environment
cp .env.example .env

# 2. Build and start containers in detached mode
docker-compose up --build -d

# 3. Verify container health status
docker-compose ps
```

### Services Defined:
1. `postgres`: PostgreSQL 16 Alpine container with persistent named volume `postgres_data` and automatic `pg_isready` healthcheck.
2. `backend`: FastAPI Python application with automated Alembic migrations on startup (`alembic upgrade head`) and background scheduler.
3. `frontend`: High-performance Nginx Alpine container serving minified React assets with client-side SPA routing.

---

## 4. Kubernetes / MeghRaj Cloud Manifests

For cloud deployment on National Informatics Centre (NIC) MeghRaj or National Cloud:

### 4.1 Liveness & Readiness Probes:
- **Liveness Probe**: `GET /health/live` (port 8000)
  - `initialDelaySeconds: 10`
  - `periodSeconds: 15`
  - `timeoutSeconds: 3`
- **Readiness Probe**: `GET /health/ready` (port 8000)
  - `initialDelaySeconds: 5`
  - `periodSeconds: 10`
  - Verifies database socket connection and storage write permissions.

---

## 5. Persistent Job Recovery & Scheduler Operations

SETU includes a background scheduler (`backend/app/services/scheduler.py`) that operates continuously:
- **Periodic Jobs**:
  1. `SLA_DEADLINE_EVALUATION`: Evaluates stage deadlines, updates urgency meters, and enqueues overdue alerts.
  2. `NOTIFICATION_OUTBOX_DISPATCH`: Processes queued notifications and executes exponential backoff retries.
- **Missed Job Recovery**:
  - On application startup or restart, the scheduler inspects `JobExecution` history.
  - If any job has not executed within 2x its expected interval, an immediate catch-up run (`*_CATCHUP_RECOVERY`) is executed and recorded in the database ledger.
- **Observability**:
  - Live job execution history is queryable at `GET /health/jobs`.
