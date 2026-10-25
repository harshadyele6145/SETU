from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from backend.app.models.application import Application
from backend.app.models.region import Region
from backend.app.models.institution import Institution
from backend.app.models.compliance import ComplianceObligation
from backend.app.models.document import DocumentRegistry
from backend.app.models.alert import Alert
from backend.app.models.user import User


class DashboardService:
    @staticmethod
    def get_dashboard_metrics(db: Session, user: User) -> Dict[str, Any]:
        """
        Dynamically computes all dashboard metrics from the database without any hardcoded counts.
        Respects user role and data isolation scopes.
        """
        app_q = db.query(Application)
        ob_q = db.query(ComplianceObligation)
        doc_q = db.query(DocumentRegistry)
        alert_q = db.query(Alert)

        # Apply Scoping
        if user.role == "INST_ADMIN":
            app_q = app_q.filter(Application.institution_id == user.institution_id)
            ob_q = ob_q.filter(ComplianceObligation.institution_id == user.institution_id)
            doc_q = doc_q.filter(DocumentRegistry.institution_id == user.institution_id)
            alert_q = alert_q.filter(Alert.institution_id == user.institution_id)
        elif user.role in ["RO_OFFICER", "REGIONAL_DIR", "EVC_COORD"] and user.region_id:
            app_q = app_q.filter(Application.region_id == user.region_id)
            ob_q = ob_q.join(Institution).filter(Institution.region_id == user.region_id)
            doc_q = doc_q.join(Institution).filter(Institution.region_id == user.region_id)
            alert_q = alert_q.filter(Alert.region_id == user.region_id)

        # 1. Application Counts
        total_apps = app_q.count()
        approved_apps = app_q.filter(Application.status == "APPROVED").count()
        rejected_apps = app_q.filter(Application.status == "REJECTED").count()
        active_apps = app_q.filter(Application.status.notin_(["APPROVED", "REJECTED"])).count()
        clarification_apps = app_q.filter(Application.status == "PENDING_CLARIFICATION").count()

        # Route Breakdown
        routes = ["ROUTE_A", "ROUTE_B", "ROUTE_C", "ROUTE_D"]
        route_distribution = []
        for r in routes:
            count = app_q.filter(Application.route == r).count()
            route_distribution.append({"route": r, "count": count})

        # Stage Breakdown
        stage_counts = {
            "DRAFT": app_q.filter(Application.status == "DRAFT").count(),
            "SUBMITTED": app_q.filter(Application.status == "SUBMITTED").count(),
            "SCRUTINY": app_q.filter(Application.status.in_(["UNDER_SCRUTINY", "SCRUTINY_RECOMMENDED"])).count(),
            "EVC": app_q.filter(Application.status.in_(["EVC_SCHEDULED", "EVC_COMPLETED"])).count(),
            "SAC_SHC": app_q.filter(Application.status.in_(["SAC_RECOMMENDED", "SHC_SCHEDULED"])).count(),
            "DECISION": approved_apps + rejected_apps
        }

        # 2. Regional Workload Breakdown
        regional_workload = []
        all_regions = db.query(Region).order_by(Region.code).all()
        for reg in all_regions:
            # Regional breakdown queries
            reg_total = db.query(Application).filter(Application.region_id == reg.id).count()
            reg_active = db.query(Application).filter(
                Application.region_id == reg.id,
                Application.status.notin_(["APPROVED", "REJECTED"])
            ).count()
            reg_overdue = db.query(Alert).filter(
                Alert.region_id == reg.id,
                Alert.severity.in_(["HIGH", "CRITICAL"]),
                Alert.is_acknowledged.is_(False)
            ).count()

            regional_workload.append({
                "region_id": reg.id,
                "region_code": reg.code,
                "region_name": reg.name,
                "total_applications": reg_total,
                "active_applications": reg_active,
                "overdue_alerts": reg_overdue
            })

        # 3. Compliance Health
        total_obligations = ob_q.count()
        overdue_obligations = ob_q.filter(ComplianceObligation.status == "OVERDUE").count()
        due_soon_obligations = ob_q.filter(ComplianceObligation.status == "DUE_SOON").count()
        verified_obligations = ob_q.filter(ComplianceObligation.status == "VERIFIED").count()
        submitted_obligations = ob_q.filter(ComplianceObligation.status == "SUBMITTED").count()

        # 4. Document Validity
        total_documents = doc_q.count()
        expiring_documents = doc_q.filter(DocumentRegistry.status == "EXPIRING_SOON").count()
        expired_documents = doc_q.filter(DocumentRegistry.status == "EXPIRED").count()
        renewal_submitted = doc_q.filter(DocumentRegistry.status == "RENEWAL_SUBMITTED").count()

        # 5. Alert Statistics
        total_alerts = alert_q.count()
        critical_alerts = alert_q.filter(Alert.severity == "CRITICAL", Alert.is_acknowledged.is_(False)).count()
        high_alerts = alert_q.filter(Alert.severity == "HIGH", Alert.is_acknowledged.is_(False)).count()
        escalated_alerts = alert_q.filter(Alert.is_escalated.is_(True)).count()
        unacknowledged_alerts = alert_q.filter(Alert.is_acknowledged.is_(False)).count()

        return {
            "summary": {
                "total_applications": total_apps,
                "active_applications": active_apps,
                "approved_applications": approved_apps,
                "rejected_applications": rejected_apps,
                "clarification_pending": clarification_apps,
                "critical_alerts": critical_alerts,
                "unacknowledged_alerts": unacknowledged_alerts,
                "escalated_alerts": escalated_alerts,
                "overdue_obligations": overdue_obligations,
                "expired_documents": expired_documents
            },
            "route_distribution": route_distribution,
            "stage_breakdown": stage_counts,
            "regional_workload": regional_workload,
            "compliance_health": {
                "total": total_obligations,
                "overdue": overdue_obligations,
                "due_soon": due_soon_obligations,
                "submitted": submitted_obligations,
                "verified": verified_obligations
            },
            "document_health": {
                "total": total_documents,
                "expiring_soon": expiring_documents,
                "expired": expired_documents,
                "renewal_submitted": renewal_submitted
            }
        }
