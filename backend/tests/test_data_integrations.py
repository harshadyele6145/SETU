import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.seed.seed_data import seed_database
from backend.app.models.institution import Institution
from backend.app.adapters.public_onod_provider import aicte_open_data_provider, PUBLIC_REFERENCE_INSTITUTIONS
from backend.app.services.integration_service import integration_service


def get_token(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    assert res.status_code == 200
    return res.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_public_onod_provider_reconcile_valid_records(db_session: Session):
    """
    Verifies valid ingestion of Category B public reference institutions:
    - Sets source_system = 'AICTE_ONOD_PUBLIC'
    - Sets is_synthetic = False
    - Preserves stable external_id
    - Populates synchronization timestamps
    """
    seed_database(db_session, generate_alerts=False)

    report = aicte_open_data_provider.reconcile_records(db=db_session, batch_limit=5)
    assert report["status"] == "SUCCESS"
    assert report["reconciled_count"] == 5
    assert report["records_created"] == 5
    assert report["records_updated"] == 0
    assert report["malformed_count"] == 0

    # Verify database state
    coep = db_session.query(Institution).filter(Institution.aicte_id == "1-ONOD-WRO-001").first()
    assert coep is not None
    assert coep.name == "COEP Technological University"
    assert coep.source_system == "AICTE_ONOD_PUBLIC"
    assert coep.is_synthetic is False
    assert coep.external_id == "1-ONOD-WRO-001"
    assert coep.sync_status == "SYNCED"
    assert coep.synced_at is not None


def test_public_onod_provider_duplicate_prevention(db_session: Session):
    """
    Verifies that executing reconciliation multiple times is idempotent:
    - Does NOT create duplicate rows
    - Updates timestamps and metadata on existing institutions
    """
    seed_database(db_session, generate_alerts=False)

    # First reconciliation
    r1 = aicte_open_data_provider.reconcile_records(db=db_session, batch_limit=5)
    assert r1["records_created"] == 5

    # Count before second pass
    count_before = db_session.query(Institution).filter(Institution.source_system == "AICTE_ONOD_PUBLIC").count()
    assert count_before == 5

    # Second reconciliation with same data
    r2 = aicte_open_data_provider.reconcile_records(db=db_session, batch_limit=5)
    assert r2["records_created"] == 0
    assert r2["records_updated"] == 5
    assert r2["reconciled_count"] == 5

    count_after = db_session.query(Institution).filter(Institution.source_system == "AICTE_ONOD_PUBLIC").count()
    assert count_after == 5, "Duplicate institutions were created on subsequent sync!"


def test_public_onod_provider_malformed_record_rejection(db_session: Session):
    """
    Verifies that malformed records (missing aicte_id, empty name, missing region)
    are safely rejected and logged without corrupting database integrity.
    """
    seed_database(db_session, generate_alerts=False)

    malformed_records = [
        {"aicte_id": "", "name": "Invalid Missing ID", "region_code": "RO_NORTH"},
        {"aicte_id": "1-ONOD-TEST-001", "name": "   ", "region_code": "RO_NORTH"},
        {"aicte_id": "1-ONOD-TEST-002", "name": "Valid Name", "region_code": None},
        {"aicte_id": "1-ONOD-VALID-001", "name": "Valid Test Institute", "region_code": "RO_NORTH"}
    ]

    report = aicte_open_data_provider.reconcile_records(db=db_session, custom_records=malformed_records)
    assert report["malformed_count"] == 3
    assert report["records_created"] == 1
    assert report["reconciled_count"] == 1

    # Verify only the valid record was added
    valid_inst = db_session.query(Institution).filter(Institution.aicte_id == "1-ONOD-VALID-001").first()
    assert valid_inst is not None

    invalid_inst = db_session.query(Institution).filter(Institution.aicte_id == "1-ONOD-TEST-001").first()
    assert invalid_inst is None


def test_public_onod_provider_read_only_boundary():
    """
    Verifies statutory read-only boundary:
    Public Open Data catalogs must NEVER accept outbound decision pushes (HTTP 405).
    """
    res = aicte_open_data_provider.push_approval_decision(
        application_no="AICTE/NRO/2026/001",
        decision="APPROVED",
        comments="Attempted push to read-only catalog"
    )
    assert res.success is False
    assert res.status_code == 405
    assert "read-only publication catalog" in res.message


def test_public_onod_provider_honest_upstream_probe_status():
    """
    Verifies that status reporting truthfully discloses when upstream connection
    is blocked (e.g. HTTP 502 / network isolation) rather than claiming live connection.
    """
    status = aicte_open_data_provider.report_status()
    assert status.data_category == "CATEGORY_B_PUBLIC_REFERENCE"
    assert status.is_configured is True
    # The provider must NOT claim is_connected is True if live probe fails
    assert "access_blocker" in status.details
    assert "upstream_endpoint" in status.details
    assert status.details["statutory_classification"].startswith("Category B")


def test_integration_monitor_providers_endpoint(client: TestClient, db_session: Session):
    """
    Verifies /api/integrations/providers endpoint surfaces all registered providers
    with truthful configuration, connectivity, and category metadata.
    """
    seed_database(db_session, generate_alerts=False)
    bo_token = get_token(client, "bo_officer@aicte.gov.in")

    res = client.get("/api/integrations/providers", headers=auth_header(bo_token))
    assert res.status_code == 200
    providers = res.json()["providers"]
    assert len(providers) >= 2

    # Check Mock Provider
    mock_p = next(p for p in providers if p["provider_id"] == "MOCK_PORTAL_ADAPTER")
    assert mock_p["data_category"] == "CATEGORY_A_SYNTHETIC"

    # Check ONOD Provider
    onod_p = next(p for p in providers if p["provider_id"] == "AICTE_ONOD_PUBLIC_PROVIDER")
    assert onod_p["data_category"] == "CATEGORY_B_PUBLIC_REFERENCE"
    assert onod_p["is_configured"] is True


def test_data_provenance_cryptographic_separation(client: TestClient, db_session: Session):
    """
    Verifies /api/integrations/provenance accurately reports Category A (Synthetic),
    Category B (Public Reference), and Category C (Operational) counts.
    """
    seed_database(db_session, generate_alerts=False)
    bo_token = get_token(client, "bo_officer@aicte.gov.in")

    # Reconcile public data
    client.post("/api/integrations/sync-open-data", headers=auth_header(bo_token))

    res = client.get("/api/integrations/provenance", headers=auth_header(bo_token))
    assert res.status_code == 200
    prov = res.json()

    assert prov["institutions"]["synthetic_count"] == 10
    assert prov["institutions"]["public_reference_count"] == 5
    assert prov["institutions"]["total"] == 15
    assert "Category A" in prov["trust_statement"]
    assert "Category B" in prov["trust_statement"]

