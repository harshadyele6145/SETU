import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.institution import Institution
from backend.app.models.application import Application
from backend.app.models.job import JobExecution
from backend.app.models.user import User
from backend.app.adapters.mock_provider import mock_portal_provider, MockPortalProvider
from backend.app.adapters.public_onod_provider import aicte_open_data_provider, AICTEOpenDataProvider
from backend.app.services.scheduler import scheduler_service
from backend.app.services.integration_service import integration_service
from backend.seed.seed_data import seed_database


def get_token_for(client: TestClient, email: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": "DemoPass@2026"})
    return res.json()["access_token"]


def test_provenance_schema_and_defaults(client: TestClient, db_session: Session):
    """Verifies that DataProvenanceMixin columns exist and have appropriate defaults."""
    seed_database(db_session)
    inst = db_session.query(Institution).first()
    assert inst is not None
    assert hasattr(inst, "source_system")
    assert hasattr(inst, "is_synthetic")
    assert hasattr(inst, "sync_status")
    assert hasattr(inst, "synced_at")

    app_record = db_session.query(Application).first()
    assert app_record is not None
    assert hasattr(app_record, "source_system")
    assert hasattr(app_record, "is_synthetic")
    assert hasattr(app_record, "sync_status")


def test_seeded_data_marked_as_synthetic(client: TestClient, db_session: Session):
    """Verifies that all seeded demonstration records are explicitly tagged as Synthetic (Category A)."""
    seed_database(db_session)
    institutions = db_session.query(Institution).filter(Institution.source_system == "SYNTHETIC_SEED").all()
    assert len(institutions) >= 10
    for inst in institutions:
        assert inst.is_synthetic is True
        assert inst.source_system == "SYNTHETIC_SEED"

    applications = db_session.query(Application).filter(Application.source_system == "SYNTHETIC_SEED").all()
    assert len(applications) >= 20
    for a in applications:
        assert a.is_synthetic is True
        assert a.source_system == "SYNTHETIC_SEED"


def test_mock_portal_provider_contract():
    """Verifies MockPortalProvider implementation adhering to BaseIntegrationProvider."""
    provider = MockPortalProvider()
    assert provider.provider_id == "MOCK_PORTAL_ADAPTER"
    assert provider.data_category == "CATEGORY_A_SYNTHETIC"
    assert provider.validate_connectivity() is True

    # Test deterministic profile fetch
    profile = provider.fetch_institution_reference("1-100234501")
    assert profile is not None
    assert profile.aicte_id == "1-100234501"
    assert "Affiliated Technical Institute" in profile.name

    # Test push approval decision
    push_res = provider.push_approval_decision("AICTE-2026-0101", "APPROVED", "Verified EoA criteria")
    assert push_res.success is True
    assert push_res.status_code == 200
    assert push_res.external_reference_id is not None

    # Test failure mode simulation
    provider.set_simulate_failure(True)
    assert provider.validate_connectivity() is False
    with pytest.raises(ConnectionError):
        provider.fetch_institution_reference("1-100234501")
    failed_push = provider.push_approval_decision("AICTE-2026-0101", "APPROVED", "Fail test")
    assert failed_push.success is False
    assert failed_push.status_code == 504


def test_aicte_open_data_provider_public_reference():
    """Verifies AICTEOpenDataProvider for public ONOD reference datasets (Category B)."""
    provider = AICTEOpenDataProvider()
    assert provider.provider_id == "AICTE_ONOD_PUBLIC_PROVIDER"
    assert provider.data_category == "CATEGORY_B_PUBLIC_REFERENCE"
    assert provider.validate_connectivity() is True

    # Check known public reference institution (e.g. COEP Pune)
    profile = provider.fetch_institution_reference("1-ONOD-WRO-001")
    assert profile is not None
    assert profile.aicte_id == "1-ONOD-WRO-001"
    assert "COEP" in profile.name
    assert profile.state == "Maharashtra"
    assert profile.is_autonomous is True

    # Public registry is read-only for decisions
    push_res = provider.push_approval_decision("AICTE-001", "APPROVED", "Notes")
    assert push_res.success is False
    assert push_res.status_code == 405


def test_job_execution_persistence_and_missed_recovery(client: TestClient, db_session: Session):
    """Verifies persistent background job ledger and missed run recovery detection."""
    seed_database(db_session)
    job = scheduler_service.record_job_start(db_session, "TEST_SCHEDULED_JOB")
    assert job is not None
    assert job.status == "RUNNING"

    completed = scheduler_service.record_job_complete(
        db=db_session,
        job_id=job.id,
        status="SUCCESS",
        items_processed=42,
        execution_time_ms=15.5
    )
    assert completed.status == "SUCCESS"
    assert completed.items_processed == 42

    # Verify queryable from DB
    persisted = db_session.query(JobExecution).filter(JobExecution.id == job.id).first()
    assert persisted is not None
    assert persisted.job_name == "TEST_SCHEDULED_JOB"

    # Test missed job recovery check
    recovery_results = scheduler_service.check_missed_jobs_and_recover(db_session)
    assert isinstance(recovery_results, list)
    assert len(recovery_results) >= 2


def test_health_and_readiness_endpoints(client: TestClient, db_session: Session):
    """Verifies /health, /health/live, /health/ready, and /health/jobs endpoints."""
    # Liveness probe
    live_res = client.get("/health/live")
    assert live_res.status_code == 200
    assert live_res.json()["status"] == "alive"

    # Readiness probe
    ready_res = client.get("/health/ready")
    assert ready_res.status_code == 200
    assert ready_res.json()["ready"] is True
    assert ready_res.json()["database_connected"] is True

    # Jobs ledger
    jobs_res = client.get("/health/jobs")
    assert jobs_res.status_code == 200
    assert isinstance(jobs_res.json(), list)


def test_observability_middleware_headers_and_correlation(client: TestClient, db_session: Session):
    """Verifies X-Request-ID propagation and defense-in-depth security response headers."""
    custom_id = "test-corr-id-998877"
    response = client.get("/health/live", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    # When no X-Request-ID passed, middleware should auto-generate one
    response_auto = client.get("/health/live")
    assert response_auto.status_code == 200
    assert response_auto.headers.get("X-Request-ID") is not None
    assert response_auto.headers.get("X-Request-ID").startswith("req_")


def test_integration_endpoints_and_rbac_scoping(client: TestClient, db_session: Session):
    """Verifies /api/integrations/providers, /provenance, and role-scoped /sync-open-data."""
    seed_database(db_session)
    ro_token = get_token_for(client, "ro_north@aicte.gov.in")
    inst_token = get_token_for(client, "inst_admin@fictional-nist.edu.in")
    bo_token = get_token_for(client, "bo_officer@aicte.gov.in")

    # 1. Providers endpoint
    prov_res = client.get("/api/integrations/providers", headers={"Authorization": f"Bearer {ro_token}"})
    assert prov_res.status_code == 200
    providers = prov_res.json()["providers"]
    assert len(providers) >= 2

    # 2. Provenance endpoint
    prov_sum = client.get("/api/integrations/provenance", headers={"Authorization": f"Bearer {ro_token}"})
    assert prov_sum.status_code == 200
    data = prov_sum.json()
    assert "institutions" in data
    assert "applications" in data
    assert data["institutions"]["synthetic_count"] >= 10

    # 3. Scoped Sync: Institution admin should be rejected with HTTP 403 Forbidden
    sync_denied = client.post("/api/integrations/sync-open-data", headers={"Authorization": f"Bearer {inst_token}"})
    assert sync_denied.status_code == 403

    # 4. Scoped Sync: Bureau Officer authorized
    sync_ok = client.post("/api/integrations/sync-open-data", headers={"Authorization": f"Bearer {bo_token}"})
    assert sync_ok.status_code == 200
    sync_data = sync_ok.json()
    assert sync_data["status"] == "SUCCESS"
    assert sync_data["reconciled_count"] >= 1
