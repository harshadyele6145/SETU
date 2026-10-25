import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ExternalInstitutionProfile(BaseModel):
    aicte_id: str
    name: str
    region: str
    approval_status: str
    last_approved_academic_year: str
    is_autonomous: bool
    intake_capacity: int


class SyncResult(BaseModel):
    success: bool
    status_code: int
    message: str
    external_reference_id: Optional[str] = None
    timestamp: float


class IntegrationHealthStatus(BaseModel):
    adapter_name: str
    is_connected: bool
    latency_ms: float
    simulated_failure_active: bool
    details: Dict[str, Any]


class ExternalPortalAdapter(ABC):
    @abstractmethod
    def fetch_institution_profile(self, aicte_id: str) -> ExternalInstitutionProfile:
        """Fetch verified institutional master data from external AICTE portal."""
        pass

    @abstractmethod
    def push_approval_decision(self, application_no: str, decision: str, comments: str) -> SyncResult:
        """Push final approval or rejection outcome to AICTE national registry."""
        pass

    @abstractmethod
    def check_health(self) -> IntegrationHealthStatus:
        """Health check probe."""
        pass


class MockPortalAdapter(ExternalPortalAdapter):
    """
    Mock adapter fulfilling prototype demonstration requirements.
    Supports simulated success and controlled simulated failure.
    """
    def __init__(self, simulate_failure: bool = False):
        self.simulate_failure = simulate_failure
        self.call_count = 0

    def set_simulate_failure(self, fail: bool):
        self.simulate_failure = fail

    def fetch_institution_profile(self, aicte_id: str) -> ExternalInstitutionProfile:
        self.call_count += 1
        if self.simulate_failure:
            raise ConnectionError("Simulated External AICTE Gateway 503 Service Unavailable")

        return ExternalInstitutionProfile(
            aicte_id=aicte_id,
            name=f"AICTE Affiliated Technical Institute ({aicte_id})",
            region="Western",
            approval_status="APPROVED_PRIOR_CYCLE",
            last_approved_academic_year="2025-2026",
            is_autonomous=False,
            intake_capacity=420
        )

    def push_approval_decision(self, application_no: str, decision: str, comments: str) -> SyncResult:
        self.call_count += 1
        now = time.time()
        if self.simulate_failure:
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

    def check_health(self) -> IntegrationHealthStatus:
        return IntegrationHealthStatus(
            adapter_name="MockPortalAdapter (Prototype Environment)",
            is_connected=not self.simulate_failure,
            latency_ms=12.4,
            simulated_failure_active=self.simulate_failure,
            details={
                "total_mock_calls": self.call_count,
                "environment": "SYNTHETIC_DEMO",
                "prerequisites_met": True
            }
        )


mock_portal_adapter = MockPortalAdapter()
