import os
import pytest
from pathlib import Path
from backend.storage.backup_restore import BackupManager, compute_file_sha256


def test_backup_creation_and_integrity_verification(tmp_path):
    # Initialize manager with temporary test backup directory
    backup_dir = tmp_path / "test_backups"
    manager = BackupManager(backup_dir=str(backup_dir))

    # Step 1: Create backup
    manifest = manager.create_backup()
    assert manifest["status"] == "COMPLETED"
    assert "setu_backup_" in manifest["backup_file"]
    
    backup_file_path = backup_dir / manifest["backup_file"]
    assert backup_file_path.exists()
    assert backup_file_path.stat().st_size > 0

    # Step 2: Verify checksum
    actual_hash = compute_file_sha256(str(backup_file_path))
    assert actual_hash == manifest["sha256"]

    # Step 3: Verify backup integrity and cryptographic audit hash chain
    report = manager.verify_backup(str(backup_file_path))
    assert report["valid"] is True
    assert report["audit_chain_valid"] is True
    assert report["application_count"] >= 0
    assert report["institution_count"] >= 0


def test_backup_tamper_detection(tmp_path):
    backup_dir = tmp_path / "test_backups_tamper"
    manager = BackupManager(backup_dir=str(backup_dir))

    # Create legitimate backup
    manifest = manager.create_backup()
    backup_file_path = backup_dir / manifest["backup_file"]

    # Tamper with the backup file (flip some bytes)
    with open(backup_file_path, "r+b") as f:
        f.seek(100)
        f.write(b"TAMPERED_BYTES_CORRUPTING_BACKUP")

    # Verification should catch the checksum failure
    report = manager.verify_backup(str(backup_file_path))
    assert report["valid"] is False
    assert "Checksum mismatch" in report["error"]
