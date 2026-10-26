import time
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.adapters.base_provider import (
    BaseIntegrationProvider,
    ExternalInstitutionProfile,
    SyncResult,
    IntegrationHealthStatus
)


class MockPortalProvider(BaseIntegrationProvider):
    """
    Simulated AICTE Portal Provider for controlled prototype demonstrations.
    Explicitly categorized as CATEGORY_A_SYNTHETIC.
    """

    def __init__(self, simulate_failure: bool = False):
        self._simulate_failure = simulate_failure
        self._call_count = 0

    @property
    def provider_id(self) -> str:
        return "MOCK_PORTAL_ADAPTER"

    @property
    def display_name(self) -> str:
        return "MockPortalAdapter (AICTE Central Gateway Simulation)"

    @property
    def data_category(self) -> str:
        return "CATEGORY_A_SYNTHETIC"

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def simulate_failure(self) -> bool:
        return self._simulate_failure

    def set_simulate_failure(self, fail: bool) -> None:
        self._simulate_failure = fail

    def validate_connectivity(self) -> bool:
        return not self._simulate_failure

    def fetch_institution_reference(self, aicte_id: str) -> Optional[ExternalInstitutionProfile]:
        self._call_count += 1
        if self._simulate_failure:
            raise ConnectionError("Simulated External AICTE Gateway 503 Service Unavailable")

        return ExternalInstitutionProfile(
            aicte_id=aicte_id,
            name=f"AICTE Affiliated Technical Institute ({aicte_id})",
            region="Western",
            approval_status="APPROVED_PRIOR_CYCLE",
            last_approved_academic_year="2025-2026",
            is_autonomous=False,
            intake_capacity=420,
            district="Pune",
            state="Maharashtra"
        )

    # Maintain fetch_institution_profile alias for backwards compatibility
    def fetch_institution_profile(self, aicte_id: str) -> ExternalInstitutionProfile:
        return self.fetch_institution_reference(aicte_id)

    def push_approval_decision(self, application_no: str, decision: str, comments: str) -> SyncResult:
        self._call_count += 1
        now = time.time()
        if self._simulate_failure:
            return SyncResult(
                success=False,
                status_code=504,
                message="Simulated Gateway Timeout communicating with AICTE central API.",
                timestamp=now
            )
        return SyncResult(
            success=True,
            status_code=200,
            message="Decision successfully synchronized with AICTE national database.",
            external_reference_id=f"AICTE-SYNC-{int(now)}",
            timestamp=now
        )

    def report_status(self) -> IntegrationHealthStatus:
        return IntegrationHealthStatus(
            adapter_name=self.display_name,
            is_connected=not self._simulate_failure,
            latency_ms=12.4 if not self._simulate_failure else 1250.0,
            simulated_failure_active=self._simulate_failure,
            data_category=self.data_category,
            details={
                "total_mock_calls": self._call_count,
                "environment": "SYNTHETIC_DEMO",
                "prerequisites_met": True,
                "notes": "Safe prototype simulator - does not connect to live governmental backends."
            }
        )

    def check_health(self) -> IntegrationHealthStatus:
        return self.report_status()

    def reconcile_records(self, db: Session, batch_limit: int = 50) -> Dict[str, Any]:
        return {
            "provider": self.provider_id,
            "reconciled_count": 0,
            "skipped_count": 0,
            "status": "SIMULATED_SUCCESS",
            "message": "Mock provider does not ingest live master records."
        }


mock_portal_provider = MockPortalProvider()
