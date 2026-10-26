from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from sqlalchemy.orm import Session


class ExternalInstitutionProfile(BaseModel):
    aicte_id: str
    name: str
    region: str
    approval_status: str
    last_approved_academic_year: str
    is_autonomous: bool
    intake_capacity: int
    district: Optional[str] = None
    state: Optional[str] = None
    program: Optional[str] = "Engineering & Technology"


class SyncResult(BaseModel):
    success: bool
    status_code: int
    message: str
    external_reference_id: Optional[str] = None
    timestamp: float


class IntegrationHealthStatus(BaseModel):
    adapter_name: str
    is_connected: bool
    is_configured: bool = True
    latency_ms: float
    simulated_failure_active: bool
    data_category: str  # CATEGORY_A_SYNTHETIC, CATEGORY_B_PUBLIC_REFERENCE, CATEGORY_C_REAL_OPERATIONAL
    last_sync_time: Optional[str] = None
    details: Dict[str, Any]


class BaseIntegrationProvider(ABC):
    """
    Abstract contract for external data integrations adhering to the
    SETU Data Provenance Architecture.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier for this integration provider."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name."""
        pass

    @property
    @abstractmethod
    def data_category(self) -> str:
        """Category A (SYNTHETIC_SEED), Category B (AICTE_ONOD_PUBLIC), or Category C (SETU_OPERATIONAL)."""
        pass

    @abstractmethod
    def validate_connectivity(self) -> bool:
        """Performs a lightweight probe to confirm gateway or source reachability."""
        pass

    @abstractmethod
    def fetch_institution_reference(self, aicte_id: str) -> Optional[ExternalInstitutionProfile]:
        """Fetches institutional profile data by AICTE Permanent ID."""
        pass

    @abstractmethod
    def push_approval_decision(self, application_no: str, decision: str, comments: str) -> SyncResult:
        """Synchronizes final workflow determinations upstream."""
        pass

    @abstractmethod
    def report_status(self) -> IntegrationHealthStatus:
        """Generates real-time telemetry and health metadata."""
        pass

    @abstractmethod
    def reconcile_records(self, db: Session, batch_limit: int = 50) -> Dict[str, Any]:
        """Runs periodic reconciliation of master institutional records."""
        pass

