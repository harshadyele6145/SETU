# SETU — External Integration Architecture & Provider Guide

This document specifies the provider adapter architecture, network protocols, idempotency models, and government gateway integration requirements for SETU.

---

## 1. Architectural Boundary Overview

SETU strictly decouples core workflow orchestration, statutory SLA tracking, and audit ledgers from external portal implementations through the **Adapter Pattern**:

```
+------------------------------------------------------------------------------------+
|                               SETU WORKFLOW ENGINE                                 |
+------------------------------------------------------------------------------------+
                                      |
                                      v
                      [backend/app/services/integration_service.py]
                                      |
                      +---------------+---------------+
                      |                               |
                      v                               v
        [MockPortalProvider]             [AICTEOpenDataProvider]
        * Category A: Synthetic          * Category B: Public Reference
        * In-memory prototype            * ONOD dataset parsing
        * Configurable outage toggle     * Read-only statutory sync
                      |                               |
                      +---------------+---------------+
                                      |
                         (Planned Production Gateway)
                                      v
                        [NICNationalPortalProvider]
                        * Category C: Operational
                        * Mutual TLS (mTLS) + X.509
                        * HMAC-SHA256 Signed Webhooks
```

---

## 2. BaseIntegrationProvider Contract

All integration adapters implement the abstract contract defined in `backend/app/adapters/base_provider.py`:

```python
class BaseIntegrationProvider(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique provider identifier."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider label."""

    @property
    @abstractmethod
    def data_category(self) -> str:
        """CATEGORY_A_SYNTHETIC, CATEGORY_B_PUBLIC_REFERENCE, or CATEGORY_C_REAL_OPERATIONAL."""

    @abstractmethod
    def validate_connectivity(self) -> bool:
        """Liveness probe verifying external gateway availability."""

    @abstractmethod
    def fetch_institution_reference(self, aicte_id: str) -> Optional[ExternalInstitutionProfile]:
        """Queries institutional master data by Permanent ID."""

    @abstractmethod
    def push_approval_decision(self, application_no: str, decision: str, comments: str) -> SyncResult:
        """Upstream synchronization of formal council decisions."""

    @abstractmethod
    def report_status(self) -> IntegrationHealthStatus:
        """Real-time latency, connection state, and telemetry metrics."""

    @abstractmethod
    def reconcile_records(self, db: Session, batch_limit: int = 50) -> Dict[str, Any]:
        """Batch reconciliation against upstream catalog."""
```

---

## 3. Providers Included in the Platform

### 3.1 `MockPortalProvider` (Category A: Synthetic)
- **Role**: Prototype demonstration and resilience simulation.
- **Features**:
  - Deterministic institutional profile generation for demo IDs.
  - Interactive outage toggle via `POST /api/integrations/toggle-failure` (simulates HTTP 503 Gateway Unavailable and HTTP 504 Gateway Timeout).
  - Outbox retry testing under simulated network partitions.

### 3.2 `AICTEOpenDataProvider` (Category B: Public Reference)
- **Role**: Ingestion of verified public reference data (ONOD / Open Data).
- **Features**:
  - Built-in cached catalog of verified premier technical institutions (e.g., COEP Pune, CEG Anna University Chennai, HBTU Kanpur, Jadavpur University Kolkata, GEC Raipur).
  - Reconciles master directory with deduplication by `aicte_id`.
  - Tags imported institutions with `source_system="AICTE_ONOD_PUBLIC"` and `is_synthetic=False`.
  - Immutable decision boundary: Rejects outbound pushes with HTTP 405 Method Not Allowed.

---

## 4. Production Integration Readiness Checklist (NIC & Central AICTE)

To connect SETU to live National Informatics Centre (NIC) and Central AICTE infrastructure:

1. **Mutual TLS (mTLS) Transport Security**:
   - Issue and install client X.509 certificates approved by National Informatics Centre (NIC CA).
   - Configure reverse proxy (Nginx / Envoy) with TLS 1.3 and mandatory client certificate validation.

2. **Idempotency Architecture**:
   - All inbound webhooks require header `X-Idempotency-Key: <SHA-256>` generated over `(application_no, stage_id, timestamp)`.
   - SETU verifies uniqueness against `AuditEvent` and `NotificationOutbox` to prevent duplicate stage advancements.

3. **Rate Limiting & Token Bucket Throttling**:
   - Production NIC gateways enforce 100 requests / minute per client application.
   - Background sync utilizes exponential backoff (`t_retry = base * 2^attempt`) with maximum retry limit of 3.

4. **Security & Role Scoping**:
   - Only authorized leadership roles (`BUREAU_OFFICER`, `REGIONAL_DIR`, `SYS_ADMIN`) are permitted to initiate cross-system reconciliation.
   - Institutional administrators (`INST_ADMIN`) are restricted to viewing their own institution's sync provenance.
