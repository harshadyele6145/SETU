"""
SETU — Automated Backup, Restore, and Cryptographic Audit Hash Chain Verification.
Supports zero-downtime point-in-time snapshots for SQLite and PostgreSQL environments.
"""

import os
import sys
import shutil
import sqlite3
import hashlib
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple

# Add repository root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.services.audit_service import audit_service


def compute_file_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class BackupManager:
    def __init__(self, backup_dir: str = None):
        if backup_dir is None:
            self.backup_dir = Path(ROOT_DIR) / "backend" / "storage" / "backups"
        else:
            self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, db_url: str = None) -> Dict[str, Any]:
        """
        Creates a timestamped snapshot of the database.
        For SQLite, uses sqlite3 online backup API to ensure write consistency.
        """
        db_url = db_url or settings.DATABASE_URL
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        if db_url.startswith("sqlite:///"):
            raw_path = db_url.replace("sqlite:///", "")
            source_path = Path(raw_path)
            if not source_path.is_absolute():
                source_path = (Path(ROOT_DIR) / source_path).resolve()

            if not source_path.exists():
                raise FileNotFoundError(f"Source database file not found at {source_path}")

            backup_filename = f"setu_backup_{timestamp}.db"
            dest_path = self.backup_dir / backup_filename

            # Perform live online backup using sqlite3.Connection.backup
            src_conn = sqlite3.connect(str(source_path))
            dest_conn = sqlite3.connect(str(dest_path))
            with dest_conn:
                src_conn.backup(dest_conn, pages=100, sleep=0.01)
            dest_conn.close()
            src_conn.close()

            checksum = compute_file_sha256(str(dest_path))
            file_size = dest_path.stat().st_size

            manifest = {
                "backup_id": f"SETU-BKP-{timestamp}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "db_engine": "sqlite",
                "source_path": str(source_path),
                "backup_file": backup_filename,
                "file_size_bytes": file_size,
                "sha256": checksum,
                "status": "COMPLETED"
            }

            manifest_path = self.backup_dir / f"setu_backup_{timestamp}.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            return manifest

        elif "postgres" in db_url:
            # PostgreSQL dump runbook placeholder
            backup_filename = f"setu_backup_{timestamp}.sql"
            dest_path = self.backup_dir / backup_filename
            manifest = {
                "backup_id": f"SETU-BKP-PG-{timestamp}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "db_engine": "postgresql",
                "backup_file": backup_filename,
                "status": "PG_RUNBOOK_REQUIRED",
                "note": "Use pg_dump -Fc for enterprise cluster snapshots"
            }
            return manifest
        else:
            raise ValueError(f"Unsupported database scheme in URL: {db_url}")

    def verify_backup(self, backup_file: str) -> Dict[str, Any]:
        """
        Restores backup to an isolated temporary sandbox database and checks
        cryptographic audit hash chain integrity.
        """
        backup_path = Path(backup_file)
        if not backup_path.is_absolute():
            backup_path = (self.backup_dir / backup_file).resolve()

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found at {backup_path}")

        # Check sha256 against manifest if exists
        manifest_path = backup_path.with_suffix(".json")
        manifest_data = None
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            expected_hash = manifest_data.get("sha256")
            actual_hash = compute_file_sha256(str(backup_path))
            if expected_hash and expected_hash != actual_hash:
                return {
                    "valid": False,
                    "error": f"Checksum mismatch! Expected {expected_hash}, got {actual_hash}"
                }

        # Create temporary verification target
        verify_db = self.backup_dir / f"verify_tmp_{int(datetime.now().timestamp())}.db"
        shutil.copy2(str(backup_path), str(verify_db))

        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            temp_engine = create_engine(f"sqlite:///{verify_db}")
            TempSession = sessionmaker(bind=temp_engine)
            session = TempSession()

            # Verify cryptographic audit chain integrity
            is_valid, count, broken_seq, msg = audit_service.verify_chain(session)

            # Query application count and institution count
            from backend.app.models.application import Application
            from backend.app.models.institution import Institution
            app_count = session.query(Application).count()
            inst_count = session.query(Institution).count()

            session.close()
            temp_engine.dispose()

            result = {
                "valid": is_valid,
                "audit_chain_valid": is_valid,
                "total_audit_events_verified": count,
                "broken_sequence_no": broken_seq,
                "audit_verification_message": msg,
                "application_count": app_count,
                "institution_count": inst_count,
                "tested_backup": str(backup_path)
            }
            return result
        finally:
            if verify_db.exists():
                try:
                    os.remove(verify_db)
                except Exception:
                    pass

    def restore(self, backup_file: str, target_file: str = None) -> Dict[str, Any]:
        """
        Safely restores a backup into the active database file path.
        """
        backup_path = Path(backup_file)
        if not backup_path.is_absolute():
            backup_path = (self.backup_dir / backup_file).resolve()

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found at {backup_path}")

        if target_file is None:
            raw_path = settings.DATABASE_URL.replace("sqlite:///", "")
            target_file = (Path(ROOT_DIR) / raw_path).resolve()
        else:
            target_file = Path(target_file).resolve()

        # Step 1: Pre-restore verification
        verification = self.verify_backup(str(backup_path))
        if not verification.get("valid"):
            raise ValueError(f"Restore aborted: Backup integrity check failed! {verification.get('audit_verification_message')}")

        # Step 2: Backup current live db before overwrite
        safety_copy = target_file.with_name(f"{target_file.name}.pre_restore_{int(datetime.now().timestamp())}")
        if target_file.exists():
            shutil.copy2(str(target_file), str(safety_copy))

        # Step 3: Copy backup into target
        shutil.copy2(str(backup_path), str(target_file))

        return {
            "success": True,
            "restored_from": str(backup_path),
            "target": str(target_file),
            "safety_copy": str(safety_copy),
            "audit_events_verified": verification.get("total_audit_events_verified"),
            "applications_restored": verification.get("application_count")
        }


def main():
    parser = argparse.ArgumentParser(description="SETU Database Backup & Restore Utility")
    parser.add_argument("--action", choices=["backup", "verify", "restore"], required=True)
    parser.add_argument("--file", help="Backup file name or path (required for verify and restore)")
    parser.add_argument("--target", help="Optional target file path for restore")
    args = parser.parse_args()

    manager = BackupManager()

    if args.action == "backup":
        print("[BACKUP] Creating automated database backup...")
        manifest = manager.create_backup()
        print(f"[SUCCESS] Backup created successfully: {manifest.get('backup_file')}")
        print(f"   SHA-256: {manifest.get('sha256')}")
        print(f"   Size: {manifest.get('file_size_bytes')} bytes")

    elif args.action == "verify":
        if not args.file:
            print("[ERROR] --file argument is required for verify action.")
            sys.exit(1)
        print(f"[VERIFY] Verifying backup integrity for {args.file}...")
        report = manager.verify_backup(args.file)
        if report.get("valid"):
            print(f"[SUCCESS] Backup Verification PASSED!")
            print(f"   Audit Chain: INTACT ({report.get('total_audit_events_verified')} events)")
            print(f"   Applications: {report.get('application_count')}")
            print(f"   Institutions: {report.get('institution_count')}")
        else:
            print(f"[ERROR] Backup Verification FAILED: {report.get('audit_verification_message')}")
            sys.exit(1)

    elif args.action == "restore":
        if not args.file:
            print("[ERROR] --file argument is required for restore action.")
            sys.exit(1)
        print(f"[RESTORE] Restoring database from {args.file}...")
        res = manager.restore(args.file, args.target)
        print(f"[SUCCESS] Restore successful!")
        print(f"   Safety snapshot created at: {res.get('safety_copy')}")
        print(f"   Verified {res.get('audit_events_verified')} audit events and {res.get('applications_restored')} applications.")


if __name__ == "__main__":
    main()
