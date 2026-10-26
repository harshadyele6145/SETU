import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.adapters.base_provider import BaseIntegrationProvider, ExternalInstitutionProfile, SyncResult
from backend.app.adapters.mock_provider import mock_portal_provider
from backend.app.adapters.public_onod_provider import aicte_open_data_provider
from backend.app.models.institution import Institution
from backend.app.models.application import Application
from backend.app.services.audit_service import audit_service


class IntegrationService:
    def __init__(self):
        self.providers: Dict[str, BaseIntegrationProvider] = {
            mock_portal_provider.provider_id: mock_portal_provider,
            aicte_open_data_provider.provider_id: aicte_open_data_provider,
        }

    def get_providers_status(self) -> List[Dict[str, Any]]:
        results = []
        for pid, provider in self.providers.items():
            health = provider.report_status()
            results.append({
                "provider_id": pid,
                "display_name": provider.display_name,
                "data_category": provider.data_category,
                "is_connected": health.is_connected,
                "latency_ms": health.latency_ms,
                "simulated_failure_active": health.simulated_failure_active,
                "details": health.details
            })
        return results

    def get_provenance_breakdown(self, db: Session) -> Dict[str, Any]:
        """
        Calculates real-time provenance breakdown across all institutional and
        application entities in the database.
        """
        # Institutions breakdown
        inst_query = db.query(
            Institution.source_system,
            Institution.is_synthetic,
            func.count(Institution.id)
        ).group_by(Institution.source_system, Institution.is_synthetic).all()

        inst_breakdown = {
            "synthetic_count": 0,
            "public_reference_count": 0,
            "operational_count": 0,
            "total": 0,
            "by_source": {}
        }
        for src, is_synth, cnt in inst_query:
            inst_breakdown["total"] += cnt
            inst_breakdown["by_source"][src] = cnt
            if is_synth or src == "SYNTHETIC_SEED":
                inst_breakdown["synthetic_count"] += cnt
            elif src == "AICTE_ONOD_PUBLIC":
                inst_breakdown["public_reference_count"] += cnt
            else:
                inst_breakdown["operational_count"] += cnt

        # Applications breakdown
        app_query = db.query(
            Application.source_system,
            Application.is_synthetic,
            func.count(Application.id)
        ).group_by(Application.source_system, Application.is_synthetic).all()

        app_breakdown = {
            "synthetic_count": 0,
            "public_reference_count": 0,
            "operational_count": 0,
            "total": 0,
            "by_source": {}
        }
        for src, is_synth, cnt in app_query:
            app_breakdown["total"] += cnt
            app_breakdown["by_source"][src] = cnt
            if is_synth or src == "SYNTHETIC_SEED":
                app_breakdown["synthetic_count"] += cnt
            elif src == "AICTE_ONOD_PUBLIC":
                app_breakdown["public_reference_count"] += cnt
            else:
                app_breakdown["operational_count"] += cnt

        return {
            "institutions": inst_breakdown,
            "applications": app_breakdown,
            "trust_statement": "SETU enforces cryptographic data provenance: Synthetic Seed (Category A), Public Reference (Category B), and Operational (Category C) are transparently partitioned."
        }

    def sync_public_open_data(self, db: Session, actor_id: Optional[str] = None, actor_role: Optional[str] = None) -> Dict[str, Any]:
        """
        Pulls official public reference institutions from the AICTE Open Data provider.
        """
        report = aicte_open_data_provider.reconcile_records(db=db)

        # Record audit event
        audit_service.record_event(
            db=db,
            actor_role=actor_role or "SYSTEM",
            action="PUBLIC_DATA_RECONCILIATION_SYNCED",
            entity_type="INTEGRATION_PROVIDER",
            entity_id=aicte_open_data_provider.provider_id,
            actor_id=actor_id,
            new_state="SYNC_COMPLETED",
            details={
                "provider": aicte_open_data_provider.display_name,
                "reconciled_count": report["reconciled_count"],
                "skipped_count": report["skipped_count"],
                "data_category": aicte_open_data_provider.data_category
            }
        )
        db.commit()

        return report

    def fetch_institution_profile(self, aicte_id: str) -> ExternalInstitutionProfile:
        # Check public reference dataset first
        profile = aicte_open_data_provider.fetch_institution_reference(aicte_id)
        if profile:
            return profile
        # Fallback to mock provider
        return mock_portal_provider.fetch_institution_reference(aicte_id)

    def push_approval_decision(self, application_no: str, decision: str, comments: str) -> SyncResult:
        return mock_portal_provider.push_approval_decision(
            application_no=application_no,
            decision=decision,
            comments=comments
        )


integration_service = IntegrationService()
