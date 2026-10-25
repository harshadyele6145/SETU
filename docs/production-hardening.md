# SETU — Enterprise Production Hardening & Scalability Architecture

**Platform:** SETU (AICTE Approval Operations Platform)  
**Target Environment:** NIC MeghRaj Cloud / MeitY-Empaneled Sovereign Tier-IV Datacenter  
**Architecture:** Highly Available Containerized Full-Stack Services with Distributed PostgreSQL & Redis  

---

## 1. System Topology Overview

```
                                [ Public / Institution Traffic ]
                                               │
                                               ▼
                              [ NIC Cloud Load Balancer (WAF) ]
                                    (TLS 1.3 / mTLS 2048)
                                               │
                       ┌───────────────────────┴───────────────────────┐
                       ▼                                               ▼
          [ SETU Frontend Nginx (Node 1) ]             [ SETU Frontend Nginx (Node 2) ]
          (Gzip minified, CSP, HSTS)                   (Gzip minified, CSP, HSTS)
                       │                                               │
                       └───────────────────────┬───────────────────────┘
                                               │
                                               ▼
                                  [ PgBouncer Connection Pool ]
                                               │
                       ┌───────────────────────┼───────────────────────┐
                       ▼                       ▼                       ▼
             [ FastAPI App Pod 1 ]   [ FastAPI App Pod 2 ]   [ Background Worker Pod ]
             (REST API Services)     (REST API Services)     (Deadline & Outbox Engine)
                       │                       │                       │
                       └───────────────────────┼───────────────────────┘
                                               │
                       ┌───────────────────────┴───────────────────────┐
                       ▼                                               ▼
        [ Primary PostgreSQL (Read/Write) ]           [ Hot Standby PostgreSQL (Read) ]
        - WAL Streaming                               - Streaming Replication
        - Point-in-Time Recovery                      - Failover Target
                       │                                               │
                       └───────────────────────┬───────────────────────┘
                                               │
                                               ▼
                                 [ Private S3 / MinIO Storage ]
                                 - Protected Document Blobs
                                 - Encrypted Backups & Checksums
```

---

## 2. PostgreSQL Enterprise Hardening

### 2.1 Database Configuration (`postgresql.conf`)
```ini
# Memory and Worker Tuning (Assuming 32GB RAM instance)
shared_buffers = 8GB
effective_cache_size = 24GB
maintenance_work_mem = 2GB
work_mem = 64MB
max_connections = 200

# Write-Ahead Logging & Continuous Archiving
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /mnt/wal_archive/%f && cp %p /mnt/wal_archive/%f'
max_wal_size = 16GB
min_wal_size = 2GB
checkpoint_completion_target = 0.9

# Connection Pooling
# Managed via PgBouncer with transaction-level pooling
```

### 2.2 Principle of Least Privilege (Database Roles)
```sql
-- Application runtime user (cannot drop tables or delete audit events)
CREATE ROLE setu_app WITH LOGIN PASSWORD '${DB_PASSWORD}';
GRANT CONNECT ON DATABASE setu_db TO setu_app;
GRANT USAGE ON SCHEMA public TO setu_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO setu_app;

-- Strict protection on audit ledger
REVOKE DELETE, TRUNCATE ON audit_events FROM setu_app;
REVOKE UPDATE ON audit_events FROM setu_app;
```

---

## 3. Background Processing & Worker Separation

In the prototype, APScheduler handles deadlines and notifications. In enterprise production:
1. **Queue Architecture:** Redis cluster or RabbitMQ handles message broker duties.
2. **Dedicated Background Pods:** The deadline evaluation and notification outbox worker runs in a separate process container from the HTTP request handling API pods.
3. **Idempotency Guarantees:** All worker tasks accept an `idempotency_key` (e.g. `f"{entity_type}:{entity_id}:{alert_type}:{window_day}"`). If a task is requeued after a worker restart, the key prevents duplicate email/SMS dispatch or duplicate database alert creation.

---

## 4. Protected Storage & File Management

1. **Local Prototype -> Object Storage Transition:**
   - The `StorageService` interface (`backend/app/core/storage.py`) abstracts file persistence.
   - For production, swap local disk writes with an S3-compatible backend (MinIO or NIC Object Store) using presigned download URLs with 15-minute expiration tokens.
2. **Antivirus & Malware Scanning:**
   - Integrate ClamAV scanning stream into `StorageService.save_file()` before persisting raw bytes to object storage.
3. **Encrypted at Rest:**
   - Server-side AES-256 encryption on all stored documents, inspection photographs, and PDF reports.

---

## 5. Container & Network Security

- **Non-Root Execution:** All Docker containers run under non-privileged UID 10001 (`setu_user`).
- **Read-Only Root Filesystem:** Container roots are mounted read-only; ephemeral storage is mounted on `/tmp` with `noexec,nodev,nosuid`.
- **Security Headers:** Nginx reverse proxy injects:
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self' data:; img-src 'self' data:; connect-src 'self' http://localhost:8000;`

---

## 6. Secrets Management

- **Zero Hardcoded Secrets:** Database passwords, JWT secret keys, and encryption credentials are injected strictly at runtime via environment variables or HashiCorp Vault.
- **Key Rotation Policy:** JWT signing keys rotated every 90 days. Old keys supported during a 24-hour grace window.
