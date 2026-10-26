import logging
from datetime import date, datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, false

logger = logging.getLogger("setu.dashboard")

# Canonical 6 Display Categories for the Stage Pipeline Distribution
CANONICAL_STAGE_CATEGORIES: List[Tuple[str, str]] = [
    ("DRAFT", "Draft"),
    ("SUBMITTED", "Submitted"),
    ("SCRUTINY", "Scrutiny"),
    ("EVC", "EVC Visit"),
    ("SAC_SHC", "SAC / SHC"),
    ("DECISION", "Final Decision"),
]

# Comprehensive lookup dictionary mapping real workflow stage keys, names,
# statuses, and known legacy aliases into the 6 canonical categories.
STAGE_CATEGORY_MAPPING: Dict[str, str] = {
    # 1. DRAFT
    "DRAFT": "DRAFT",
    "DRAFT_APPLICATION": "DRAFT",
    "Draft": "DRAFT",
    "Draft Application": "DRAFT",

    # 2. SUBMITTED
    "SUBMITTED": "SUBMITTED",
    "SUBMITTED_REGIONAL": "SUBMITTED",
    "INTAKE": "SUBMITTED",
    "REGIONAL_INTAKE": "SUBMITTED",
    "Submitted": "SUBMITTED",
    "Submitted / Regional Intake": "SUBMITTED",

    # 3. SCRUTINY
    "SCRUTINY": "SCRUTINY",
    "UNDER_SCRUTINY": "SCRUTINY",
    "SCRUTINY_DEFICIENT": "SCRUTINY",
    "SCRUTINY_RECOMMENDED": "SCRUTINY",
    "SCRUTINY_IN_PROGRESS": "SCRUTINY",
    "SCRUTINY_COMPLETED": "SCRUTINY",
    "PENDING_CLARIFICATION": "SCRUTINY",
    "DEFICIENCY_COMMUNICATED": "SCRUTINY",
    "CLARIFICATION_REQUESTED": "SCRUTINY",
    "Scrutiny": "SCRUTINY",
    "Under Scrutiny": "SCRUTINY",
    "Scrutiny in Progress": "SCRUTINY",
    "Clarification Requested": "SCRUTINY",
    "Scrutiny Cleared / Review": "SCRUTINY",
    "Scrutiny Cleared": "SCRUTINY",

    # 4. EVC VISIT
    "EVC": "EVC",
    "EVC_QUEUE": "EVC",
    "EVC_SCHEDULED": "EVC",
    "EVC_COMPLETED": "EVC",
    "EVC_REPORT_SUBMITTED": "EVC",
    "EVC_INSPECTION": "EVC",
    "EVC_VISIT": "EVC",
    "EVC Visit": "EVC",
    "Awaiting EVC Scheduling": "EVC",
    "EVC Inspection Scheduled": "EVC",
    "Visit Conducted / Report Awaited": "EVC",
    "EVC Visit Done": "EVC",
    "Report Under Review": "EVC",
    "EVC Inspection": "EVC",
    "Inspection Scheduled": "EVC",
    "EVC Report Submitted": "EVC",

    # 5. SAC / SHC
    "SAC_SHC": "SAC_SHC",
    "SHC_QUEUE": "SAC_SHC",
    "SAC_APPEAL": "SAC_SHC",
    "SHC_HEARING": "SAC_SHC",
    "SAC_HEARING": "SAC_SHC",
    "SHC": "SAC_SHC",
    "SAC": "SAC_SHC",
    "SAC_RECOMMENDED": "SAC_SHC",
    "SHC_RECOMMENDED": "SAC_SHC",
    "SAC / SHC": "SAC_SHC",
    "Standing Hearing Committee": "SAC_SHC",
    "Standing Appellate Committee": "SAC_SHC",
    "SAC Recommendation": "SAC_SHC",
    "SHC Queue": "SAC_SHC",
    "SAC Appeal": "SAC_SHC",

    # 6. FINAL DECISION (Active pending-decision queue only, excluding completed APPROVED/REJECTED)
    "DECISION": "DECISION",
    "DECISION_PENDING": "DECISION",
    "COMPETENT_AUTHORITY_QUEUE": "DECISION",
    "COMPETENT_AUTH": "DECISION",
    "PENDING_DECISION": "DECISION",
    "Final Decision": "DECISION",
    "Decision Pending": "DECISION",
    "Decision Pending (Competent Auth)": "DECISION",
    "Competent Authority Review": "DECISION",
}

from backend.app.models.application import Application
from backend.app.models.compliance import ComplianceObligation, ComplianceEvidence
from backend.app.models.document import DocumentRegistry
from backend.app.models.alert import Alert
from backend.app.models.region import Region
from backend.app.models.institution import Institution
from backend.app.models.evc import EVCVisit, EVCExpert
from backend.app.models.user import User
from backend.app.models.base import utc_now


class DashboardService:
    @classmethod
    def map_stage_to_category(cls, stage_identifier: Optional[str]) -> Optional[str]:
        """
        Maps a stage key, stage name, or status string to one of the 6 canonical categories:
        ['DRAFT', 'SUBMITTED', 'SCRUTINY', 'EVC', 'SAC_SHC', 'DECISION'].
        Returns None for terminal states (APPROVED, REJECTED) or unrecognized values.
        """
        if not stage_identifier:
            return None
        clean = stage_identifier.strip()
        if clean in ["APPROVED", "REJECTED", "Approved", "Rejected"]:
            return None
        return STAGE_CATEGORY_MAPPING.get(clean) or STAGE_CATEGORY_MAPPING.get(clean.upper())

    @classmethod
    def classify_application_stage(cls, app: Application) -> Tuple[Optional[str], Optional[str]]:
        """
        Deterministically maps an active application to one of the 6 canonical categories:
        ['DRAFT', 'SUBMITTED', 'SCRUTINY', 'EVC', 'SAC_SHC', 'DECISION'].
        Returns (category_key, source_value).
        Completed terminal applications (APPROVED, REJECTED) return (None, status).
        """
        # Exclude completed terminal decisions from pipeline categories
        if app.status in ["APPROVED", "REJECTED"]:
            return None, app.status

        # Priority 1: Check current_stage.stage_key
        if app.current_stage:
            if app.current_stage.is_terminal:
                return None, app.current_stage.stage_key
            s_key = app.current_stage.stage_key
            if s_key in STAGE_CATEGORY_MAPPING:
                return STAGE_CATEGORY_MAPPING[s_key], s_key
            # Priority 2: Check current_stage.name
            s_name = app.current_stage.name
            if s_name in STAGE_CATEGORY_MAPPING:
                return STAGE_CATEGORY_MAPPING[s_name], s_name

        # Priority 3: Fallback to app.status
        if app.status and app.status in STAGE_CATEGORY_MAPPING:
            return STAGE_CATEGORY_MAPPING[app.status], app.status

        # Unrecognized stage/status
        unknown_val = (app.current_stage.stage_key if app.current_stage else None) or app.status
        return "UNKNOWN", unknown_val

    @staticmethod
    def get_dashboard_stats(db: Session, user: User) -> Dict[str, Any]:
        """
        Dynamically computes all dashboard metrics from the database with strict
        server-enforced scoping and customized, role-tailored operational queues.
        """
        now = utc_now()
        today = date.today()

        app_q = db.query(Application)
        ob_q = db.query(ComplianceObligation)
        doc_q = db.query(DocumentRegistry)
        alert_q = db.query(Alert)

        # -------------------------------------------------------------
        # 1. STRICT SERVER-SIDE SCOPE ENFORCEMENT
        # -------------------------------------------------------------
        # Cross-regional totals are authorized ONLY for explicit oversight roles
        CROSS_REGIONAL_ROLES = {"BUREAU_OFFICER", "BO_OFFICER", "COMP_AUTH", "SYS_ADMIN", "COMP_REV", "COMP_REVIEW"}
        is_cross_regional = user.role in CROSS_REGIONAL_ROLES

        if user.role == "INST_ADMIN":
            # Missing scope check: never fall back to unrestricted data
            if not user.institution_id:
                app_q = app_q.filter(false())
                ob_q = ob_q.filter(false())
                doc_q = doc_q.filter(false())
                alert_q = alert_q.filter(false())
            else:
                app_q = app_q.filter(Application.institution_id == user.institution_id)
                ob_q = ob_q.filter(ComplianceObligation.institution_id == user.institution_id)
                doc_q = doc_q.filter(DocumentRegistry.institution_id == user.institution_id)
                alert_q = alert_q.filter(Alert.institution_id == user.institution_id)

        elif user.role in ["RO_OFFICER", "REGIONAL_DIR", "EVC_COORD"]:
            # Missing region check: never fall back to unrestricted data
            if not user.region_id:
                app_q = app_q.filter(false())
                ob_q = ob_q.filter(false())
                doc_q = doc_q.filter(false())
                alert_q = alert_q.filter(false())
            else:
                app_q = app_q.filter(Application.region_id == user.region_id)
                ob_q = ob_q.join(Institution, ComplianceObligation.institution_id == Institution.id).filter(Institution.region_id == user.region_id)
                doc_q = doc_q.join(Institution, DocumentRegistry.institution_id == Institution.id).filter(Institution.region_id == user.region_id)
                alert_q = alert_q.filter(Alert.region_id == user.region_id)

        elif user.role in ["COMMITTEE_MBR", "COMM_MEMBER"]:
            # Committee members are strictly restricted to applications and data for their assigned inspection visits
            assigned_app_ids = [
                row[0] for row in db.query(EVCVisit.application_id)
                .join(EVCExpert)
                .filter(EVCExpert.contact_email == user.email)
                .all()
            ]
            if not assigned_app_ids:
                app_q = app_q.filter(false())
                ob_q = ob_q.filter(false())
                doc_q = doc_q.filter(false())
                alert_q = alert_q.filter(false())
            else:
                app_q = app_q.filter(Application.id.in_(assigned_app_ids))
                ob_q = ob_q.filter(ComplianceObligation.application_id.in_(assigned_app_ids))
                doc_q = doc_q.filter(DocumentRegistry.application_id.in_(assigned_app_ids))
                alert_q = alert_q.filter(Alert.entity_type == "APPLICATION", Alert.entity_id.in_(assigned_app_ids))

        elif user.role in ["COMP_REV", "COMP_REVIEW"]:
            # Compliance Reviewer focuses on compliance undertakings and evidence (scoped to region if assigned)
            if user.region_id:
                app_q = app_q.filter(Application.region_id == user.region_id)
                ob_q = ob_q.join(Institution, ComplianceObligation.institution_id == Institution.id).filter(Institution.region_id == user.region_id)
                doc_q = doc_q.join(Institution, DocumentRegistry.institution_id == Institution.id).filter(Institution.region_id == user.region_id)
                alert_q = alert_q.filter(Alert.region_id == user.region_id)

        # -------------------------------------------------------------
        # 2. CORE SUMMARY COUNTS
        # -------------------------------------------------------------
        total_apps = app_q.count()
        approved_apps = app_q.filter(Application.status == "APPROVED").count()
        rejected_apps = app_q.filter(Application.status == "REJECTED").count()
        active_apps = app_q.filter(Application.status.notin_(["APPROVED", "REJECTED"])).count()
        clarification_apps = app_q.filter(Application.status.in_(["DEFICIENCY_COMMUNICATED", "SCRUTINY_DEFICIENT", "PENDING_CLARIFICATION"])).count()

        critical_alerts = alert_q.filter(Alert.severity == "CRITICAL", Alert.is_acknowledged.is_(False)).count()
        unacknowledged_alerts = alert_q.filter(Alert.is_acknowledged.is_(False)).count()
        escalated_alerts = alert_q.filter(Alert.is_escalated.is_(True), Alert.is_acknowledged.is_(False)).count()

        # Route breakdown
        route_distribution = [
            {"route": r, "count": app_q.filter(Application.route == r).count()}
            for r in ["ROUTE_A", "ROUTE_B", "ROUTE_C", "ROUTE_D"]
        ]

        # Stage pipeline breakdown (scoped active applications only)
        category_counts = {cat_key: 0 for cat_key, _ in CANONICAL_STAGE_CATEGORIES}
        unmapped_records = []

        active_instances = app_q.filter(Application.status.notin_(["APPROVED", "REJECTED"])).all()
        for a in active_instances:
            cat, source_val = DashboardService.classify_application_stage(a)
            if cat in category_counts:
                category_counts[cat] += 1
            elif cat == "UNKNOWN":
                unmapped_records.append({"application_no": a.application_no, "source_value": source_val})
                logger.warning(
                    f"Unexpected workflow stage or status '{source_val}' on application {a.application_no}. Not mapped to 6 canonical categories."
                )

        stage_breakdown = {
            # Canonical uppercase stage keys expected by frontend
            "DRAFT": category_counts["DRAFT"],
            "SUBMITTED": category_counts["SUBMITTED"],
            "SCRUTINY": category_counts["SCRUTINY"],
            "EVC": category_counts["EVC"],
            "SAC_SHC": category_counts["SAC_SHC"],
            "DECISION": category_counts["DECISION"],
            # Category display labels
            "Draft": category_counts["DRAFT"],
            "Submitted": category_counts["SUBMITTED"],
            "Scrutiny": category_counts["SCRUTINY"],
            "EVC Visit": category_counts["EVC"],
            "SAC / SHC": category_counts["SAC_SHC"],
            "Final Decision": category_counts["DECISION"],
            # Granular/legacy aliases
            "Under Scrutiny": category_counts["SCRUTINY"],
            "EVC Inspection": category_counts["EVC"],
            "SAC Recommendation": category_counts["SAC_SHC"],
            "Decision Pending": category_counts["DECISION"],
        }
        if unmapped_records:
            stage_breakdown["_unmapped_count"] = len(unmapped_records)
            stage_breakdown["_unmapped_records"] = unmapped_records

        stage_distribution = [
            {"stage_key": cat_key, "stage": label, "count": category_counts[cat_key]}
            for cat_key, label in CANONICAL_STAGE_CATEGORIES
        ]

        # -------------------------------------------------------------
        # 3. REGIONAL WORKLOAD (Strict Data Isolation)
        # -------------------------------------------------------------
        # Institution Admins and Committee Members NEVER see regional workload tables!
        # Region-scoped roles (RO_OFFICER, REGIONAL_DIR, EVC_COORD) ONLY see their assigned region!
        # Cross-regional roles see all regions.
        regional_workload = []
        if user.role not in ["INST_ADMIN", "COMMITTEE_MBR", "COMM_MEMBER"]:
            if is_cross_regional:
                regions_to_query = db.query(Region).order_by(Region.code).all()
            elif user.region_id:
                regions_to_query = db.query(Region).filter(Region.id == user.region_id).all()
            else:
                regions_to_query = []

            for reg in regions_to_query:
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

        # -------------------------------------------------------------
        # 4. COMPLIANCE & DOCUMENT HEALTH
        # -------------------------------------------------------------
        total_obligations = ob_q.count()
        overdue_obligations = ob_q.filter(ComplianceObligation.status == "OVERDUE").count()
        due_soon_obligations = ob_q.filter(ComplianceObligation.status == "DUE_SOON").count()
        verified_obligations = ob_q.filter(ComplianceObligation.status == "VERIFIED").count()
        submitted_obligations = ob_q.filter(ComplianceObligation.status == "SUBMITTED").count()

        total_documents = doc_q.count()
        expiring_documents = doc_q.filter(DocumentRegistry.status == "EXPIRING_SOON").count()
        expired_documents = doc_q.filter(DocumentRegistry.status == "EXPIRED").count()
        renewal_submitted = doc_q.filter(DocumentRegistry.status == "RENEWAL_SUBMITTED").count()

        # -------------------------------------------------------------
        # 5. ROLE-SPECIFIC WORKSPACE ADAPTATION
        # -------------------------------------------------------------
        role_view: Dict[str, Any] = {
            "role": user.role,
            "role_title": user.role
        }

        if user.role == "INST_ADMIN":
            inst = db.get(Institution, user.institution_id) if user.institution_id else None
            role_view["institution_name"] = inst.name if inst else "Assigned Institution"

            # 1. Deficiency Notices (Requires Resubmission Action)
            deficiencies = app_q.filter(
                Application.status.in_(["DEFICIENCY_COMMUNICATED", "SCRUTINY_DEFICIENT", "PENDING_CLARIFICATION"])
            ).all()
            role_view["deficiency_notices"] = [
                {
                    "id": a.id,
                    "application_no": a.application_no,
                    "route": a.route,
                    "status": a.status,
                    "current_stage": a.current_stage.name if a.current_stage else "Scrutiny",
                    "return_count": a.return_count,
                    "sla_deadline": a.current_sla_deadline.isoformat() if a.current_sla_deadline else None
                }
                for a in deficiencies
            ]

            # 2. Pending Compliance Evidence Required
            pending_obs = ob_q.filter(ComplianceObligation.status.in_(["PENDING", "DUE_SOON", "OVERDUE", "DEFICIENT"])).all()
            role_view["pending_compliance"] = [
                {
                    "id": ob.id,
                    "title": ob.title,
                    "category": ob.category,
                    "due_date": ob.due_date.isoformat(),
                    "status": ob.status,
                    "days_remaining": (ob.due_date - today).days
                }
                for ob in pending_obs
            ]

            # 3. Document Expiry Reminders
            exp_docs = doc_q.filter(DocumentRegistry.status.in_(["EXPIRING_SOON", "EXPIRED", "RENEWAL_SUBMITTED"])).all()
            role_view["document_reminders"] = [
                {
                    "id": d.id,
                    "title": d.title,
                    "document_category": d.document_category,
                    "expiry_date": d.expiry_date.isoformat() if d.expiry_date else "N/A",
                    "status": d.status,
                    "days_to_expiry": (d.expiry_date - today).days if d.expiry_date else 0
                }
                for d in exp_docs
            ]

            # 4. My Applications Quick List
            role_view["my_applications"] = [
                {
                    "id": a.id,
                    "application_no": a.application_no,
                    "route": a.route,
                    "status": a.status,
                    "stage_name": a.current_stage.name if a.current_stage else a.status,
                    "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None
                }
                for a in app_q.order_by(desc(Application.submitted_at)).limit(8).all()
            ]

        elif user.role in ["RO_OFFICER", "REGIONAL_DIR"]:
            reg = db.get(Region, user.region_id) if user.region_id else None
            role_view["region_name"] = reg.name if reg else "Assigned Regional Office"

            # 1. Scrutiny Queue (Submitted, Under Scrutiny, Resubmitted)
            scrutiny_apps = app_q.filter(
                Application.status.in_(["SUBMITTED", "UNDER_SCRUTINY", "RESUBMITTED"])
            ).order_by(Application.stage_entered_at.asc()).all()
            role_view["scrutiny_queue"] = [
                {
                    "id": a.id,
                    "application_no": a.application_no,
                    "institution_name": a.institution.name if a.institution else "N/A",
                    "route": a.route,
                    "status": a.status,
                    "stage_age_days": max(0, (now - (a.stage_entered_at if a.stage_entered_at.tzinfo else a.stage_entered_at.replace(tzinfo=timezone.utc))).days) if a.stage_entered_at else 0,
                    "return_count": a.return_count
                }
                for a in scrutiny_apps
            ]

            # 2. Deficiency Returns List
            returned_apps = app_q.filter(
                Application.status.in_(["DEFICIENCY_COMMUNICATED", "SCRUTINY_DEFICIENT"])
            ).all()
            role_view["deficiency_returns"] = [
                {
                    "id": a.id,
                    "application_no": a.application_no,
                    "institution_name": a.institution.name if a.institution else "N/A",
                    "return_count": a.return_count
                }
                for a in returned_apps
            ]

            # 3. Urgent SLA Deadlines
            role_view["urgent_deadlines"] = [
                {
                    "id": a.id,
                    "application_no": a.application_no,
                    "institution_name": a.institution.name if a.institution else "N/A",
                    "deadline": a.current_sla_deadline.isoformat() if a.current_sla_deadline else "N/A",
                    "status": a.status
                }
                for a in app_q.filter(Application.current_sla_deadline.isnot(None), Application.status.notin_(["APPROVED", "REJECTED"])).order_by(Application.current_sla_deadline.asc()).limit(5).all()
            ]

        elif user.role == "EVC_COORD":
            # EVC Coordinator prioritization
            visits_q = db.query(EVCVisit).join(Application)
            if user.region_id:
                visits_q = visits_q.filter(Application.region_id == user.region_id)

            role_view["awaiting_schedule"] = [
                {
                    "visit_id": v.id,
                    "application_no": v.application.application_no,
                    "institution_name": v.application.institution.name if v.application.institution else "N/A",
                    "created_at": v.created_at.isoformat()
                }
                for v in visits_q.filter(EVCVisit.status == "AWAITING_SCHEDULE").limit(8).all()
            ]
            role_view["pending_reports"] = [
                {
                    "visit_id": v.id,
                    "application_no": v.application.application_no,
                    "institution_name": v.application.institution.name if v.application.institution else "N/A",
                    "completed_date": v.completed_date.isoformat() if v.completed_date else "N/A"
                }
                for v in visits_q.filter(EVCVisit.status == "COMPLETED").limit(8).all()
            ]

        elif user.role in ["COMMITTEE_MBR", "COMM_MEMBER"]:
            # Assigned visits only
            my_visits = (
                db.query(EVCVisit)
                .join(EVCExpert)
                .join(Application)
                .filter(EVCExpert.contact_email == user.email)
                .all()
            )
            role_view["assigned_inspections"] = [
                {
                    "visit_id": v.id,
                    "application_no": v.application.application_no,
                    "institution_name": v.application.institution.name if v.application.institution else "N/A",
                    "status": v.status,
                    "confirmed_date": v.confirmed_date.isoformat() if v.confirmed_date else (v.proposed_date.isoformat() if v.proposed_date else "TBD"),
                    "report_submitted": v.report_submitted_date is not None
                }
                for v in my_visits
            ]

        elif user.role in ["COMP_REV", "COMP_REVIEW"]:
            # Submitted evidence awaiting verification
            evidence_q = db.query(ComplianceEvidence).filter(ComplianceEvidence.verification_status == "SUBMITTED")
            if user.region_id:
                evidence_q = evidence_q.join(ComplianceObligation).join(Institution, ComplianceObligation.institution_id == Institution.id).filter(Institution.region_id == user.region_id)

            role_view["evidence_awaiting_verification"] = [
                {
                    "evidence_id": ev.id,
                    "obligation_title": ev.obligation.title if ev.obligation else "Undertaking",
                    "institution_name": ev.obligation.institution.name if (ev.obligation and ev.obligation.institution) else "N/A",
                    "file_name": ev.file_name,
                    "submission_date": ev.submission_date.isoformat() if ev.submission_date else None
                }
                for ev in evidence_q.limit(10).all()
            ]

        elif user.role == "COMP_AUTH":
            # Applications awaiting final statutory decision
            dec_pending = db.query(Application).filter(
                Application.status.in_(["DECISION_PENDING", "SAC_RECOMMENDED", "SHC_RECOMMENDED", "SCRUTINY_RECOMMENDED"])
            ).order_by(desc(Application.stage_entered_at)).all()

            role_view["awaiting_statutory_decision"] = [
                {
                    "id": a.id,
                    "application_no": a.application_no,
                    "institution_name": a.institution.name if a.institution else "N/A",
                    "region_name": a.region.name if a.region else "N/A",
                    "route": a.route,
                    "status": a.status,
                    "return_count": a.return_count
                }
                for a in dec_pending
            ]

            recent_decisions = db.query(Application).filter(
                Application.status.in_(["APPROVED", "REJECTED"])
            ).order_by(desc(Application.updated_at)).limit(5).all()

            role_view["recent_decisions"] = [
                {
                    "id": a.id,
                    "application_no": a.application_no,
                    "institution_name": a.institution.name if a.institution else "N/A",
                    "decision": a.status,
                    "decided_at": a.updated_at.isoformat() if a.updated_at else None
                }
                for a in recent_decisions
            ]

        elif user.role in ["BUREAU_OFFICER", "BO_OFFICER"]:
            # National oversight view
            role_view["national_summary"] = {
                "total_active_national": active_apps,
                "critical_national_alerts": critical_alerts,
                "overdue_undertakings_national": overdue_obligations
            }

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
            "stage_breakdown": stage_breakdown,
            "stage_distribution": stage_distribution,
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
            },
            "role_view": role_view
        }

    # Alias for backwards compatibility
    get_dashboard_metrics = get_dashboard_stats
