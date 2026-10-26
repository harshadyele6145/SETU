from backend.app.adapters.base_provider import (
    BaseIntegrationProvider,
    ExternalInstitutionProfile,
    SyncResult,
    IntegrationHealthStatus,
)
from backend.app.adapters.mock_provider import (
    MockPortalProvider,
    mock_portal_provider,
)

# Backwards compatibility aliases
ExternalPortalAdapter = BaseIntegrationProvider
MockPortalAdapter = MockPortalProvider
mock_portal_adapter = mock_portal_provider

__all__ = [
    "ExternalInstitutionProfile",
    "SyncResult",
    "IntegrationHealthStatus",
    "ExternalPortalAdapter",
    "MockPortalAdapter",
    "mock_portal_adapter",
]
