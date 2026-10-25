# SETU — Automated Backup, Point-in-Time Recovery, and Integrity Runbook

## 1. Overview and Operational Requirements

In accordance with SIH26262 and Indian electronic records retention guidelines, SETU implements a dual-layer backup and verification mechanism:
1. **Physical Snapshot Consistency**: Zero-downtime point-in-time database snapshots using SQLite's online backup API (or PostgreSQL WAL archiving and `pg_dump -Fc` in enterprise deployments).
2. **Cryptographic Ledger Integrity**: Every backup includes automated verification of the sequential SHA-256 hash chain in `audit_events`. A backup is rejected if hash tampering or sequence gaps are detected.

---

## 2. Backup Architecture

```
[ Active Database: setu.db ]
         │
         ├──> [ Online Backup Engine (sqlite3.backup / pg_dump) ]
         │               │
         │               ├──> Snapshot File: setu_backup_YYYYMMDD_HHMMSS.db
         │               └──> SHA-256 Manifest: setu_backup_YYYYMMDD_HHMMSS.json
         │
         ▼
[ Verification Sandbox ]
         │
         ├── 1. SHA-256 Checksum Validation
         ├── 2. Temporary Sandboxed DB Restoration
         └── 3. AuditService.verify_chain() Hash Recalculation
```

---

## 3. Command Reference

All backup, verification, and restoration operations are managed through `backend/storage/backup_restore.py`.

### 3.1 Create a Backup
```bash
python backend/storage/backup_restore.py --action backup
```
**Output**:
- Snapshot placed in `backend/storage/backups/setu_backup_<timestamp>.db`
- Metadata manifest generated at `backend/storage/backups/setu_backup_<timestamp>.json` with timestamp, engine, size, and SHA-256 checksum.

### 3.2 Verify an Existing Backup
```bash
python backend/storage/backup_restore.py --action verify --file setu_backup_<timestamp>.db
```
**Actions Performed**:
1. Verifies SHA-256 file integrity against the metadata manifest.
2. Restores into an ephemeral sandbox database.
3. Validates that every sequence in the cryptographic audit chain matches `hashlib.sha256(canonical_event)`.
4. Reports total audited records, institutions, and application counts.

### 3.3 Restore from Backup
```bash
python backend/storage/backup_restore.py --action restore --file setu_backup_<timestamp>.db
```
**Safety Safeguards**:
1. **Pre-Restore Validation**: Fails immediately if the backup file is corrupt or has broken audit hashes.
2. **Safety Snapshot**: Automatically duplicates the current active database to `setu.db.pre_restore_<timestamp>` prior to replacing data.
3. **Atomic Replacement**: Safely copies verified snapshot to active target.

---

## 4. Enterprise PostgreSQL Disaster Recovery Runbook

When deploying in production with PostgreSQL:

### 4.1 Enterprise Continuous Archiving (WAL)
- Enable `wal_level = replica` and `archive_mode = on`.
- Stream WAL segments to dedicated cold storage (e.g. MinIO / AWS S3 S3-compatible private object store).

### 4.2 Automated Nightly Snapshots
```bash
pg_dump -h db.setu.internal -U setu_admin -d setu_db -Fc -f /backups/setu_pg_$(date +%Y%m%d_%H%M%S).dump
sha256sum /backups/setu_pg_*.dump > /backups/checksums.sha256
```

### 4.3 Recovery Point Objective (RPO) and Recovery Time Objective (RTO)
- **Target RPO**: < 15 minutes (via continuous WAL streaming).
- **Target RTO**: < 5 minutes (via hot standby or automated restore script).
- **Audit Verification Requirement**: Mandatory execution of `AuditService.verify_chain()` immediately after point-in-time recovery before traffic is enabled.
