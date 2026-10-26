from datetime import datetime, timezone, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.application import Application
from backend.app.models.compliance import ComplianceObligation
from backend.app.models.document import DocumentRegistry
from backend.app.models.evc import EVCVisit, EVCExpert
from backend.app.models.user import User
from backend.app.models.base import utc_now
from backend.app.schemas.attention import BottleneckItem, BottleneckSummary


class BottleneckService:
    @staticmethod
    def get_bottleneck_exceptions(db: Session, user: User) -> BottleneckSummary:
        """
        Bottleneck & Exception Cockpit:
        Isolates stalled items and clearly categorizes them by holding responsibility:
        'Waiting on Institution' vs 'Waiting on AICTE Internal'.
        Strictly scopes by user role, institution, region, and committee assignment.
        """
        empty_summary = BottleneckSummary(
            total_exceptions=0,
            waiting_on_institution=0,
            waiting_on_aicte=0,
            overdue_count=0,
            critical_escalations=0,
            items=[]
        )

        now = utc_now()
        items: List[BottleneckItem] = []

        # 1. Applications Query (Scoped)
        app_q = db.query(Application).filter(Application.status.notin_(["APPROVED", "REJECTED"]))
        assigned_app_ids: List[str] = []

        if user.role == "INST_ADMIN":
            if not user.institution_id:
                return empty_summary
            app_q = app_q.filter(Application.institution_id == user.institution_id)
        elif user.role in ["RO_OFFICER", "REGIONAL_DIR", "EVC_COORD"]:
            if not user.region_id:
                return empty_summary
            app_q = app_q.filter(Application.region_id == user.region_id)
        elif user.role in ["COMM_MEMBER", "COMMITTEE_MBR"]:
            assigned_app_ids = [
                row[0]
                for row in db.query(EVCVisit.application_id)
                .join(EVCExpert, EVCExpert.visit_id == EVCVisit.id)
                .filter(EVCExpert.contact_email == user.email)
                .all()
            ]
            if not assigned_app_ids:
                return empty_summary
            app_q = app_q.filter(Application.id.in_(assigned_app_ids))

        apps = app_q.all()

        for a in apps:
            stg_at = a.stage_entered_at if a.stage_entered_at.tzinfo else a.stage_entered_at.replace(tzinfo=timezone.utc)
            age_days = max(0, (now - stg_at).days)
            sla_days = a.current_stage.sla_days if a.current_stage else 15
            days_remaining = sla_days - age_days
            is_overdue = days_remaining < 0

            # Determine holding side and permissible bypass action
            if a.status in ["DRAFT", "PENDING_CLARIFICATION", "SCRUTINY_DEFICIENT", "DEFICIENCY_COMMUNICATED"]:
                holding = "WAITING_ON_INSTITUTION"
                resp = "Institution Administrator"
                blocker = f"Application pending institutional response / deficiency cure for {age_days} days."
                next_action = "Upload requested clarification/deficiency documents and commit resubmission."
            else:
                holding = "WAITING_ON_AICTE"
                resp = "Regional Office / Bureau"
                blocker = f"Case in {a.current_stage.name if a.current_stage else a.status} for {age_days} days (limit {sla_days}d)."
                next_action = "Assign committee or issue expedited scrutiny determination."

            esc_state = "CRITICAL_ESCALATION" if is_overdue and abs(days_remaining) >= 7 else (
                "SLA_BREACH" if is_overdue else "WITHIN_SLA"
            )

            # Filter exceptions: only items with age > 3 days or pending clarification or overdue
            if age_days >= 3 or a.status in ["PENDING_CLARIFICATION", "SCRUTINY_DEFICIENT", "DEFICIENCY_COMMUNICATED"] or is_overdue:
                items.append(BottleneckItem(
                    id=a.id,
                    case_type="APPLICATION",
                    reference_no=a.application_no,
                    institution_name=a.institution.name if a.institution else "N/A",
                    region_name=a.region.name if a.region else "N/A",
                    current_status=a.status,
                    holding_side=holding,
                    responsible_party=resp,
                    age_days=age_days,
                    deadline_days_remaining=days_remaining,
                    is_overdue=is_overdue,
                    escalation_state=esc_state,
                    blocker_reason=blocker,
                    next_permissible_action=next_action
                ))

        # 2. Compliance Obligations (Scoped)
        ob_q = db.query(ComplianceObligation).filter(ComplianceObligation.status.notin_(["VERIFIED", "CLOSED"]))
        if user.role == "INST_ADMIN":
            ob_q = ob_q.filter(ComplianceObligation.institution_id == user.institution_id)
        elif user.role in ["RO_OFFICER", "REGIONAL_DIR", "EVC_COORD"]:
            ob_q = ob_q.filter(ComplianceObligation.institution.has(region_id=user.region_id))
        elif user.role in ["COMM_MEMBER", "COMMITTEE_MBR"]:
            if assigned_app_ids:
                ob_q = ob_q.filter(ComplianceObligation.application_id.in_(assigned_app_ids))
            else:
                ob_q = ob_q.filter(False)

        obs = ob_q.all()
        for o in obs:
            days_rem = (o.due_date - now.date()).days
            is_overdue = days_rem < 0
            if is_overdue or o.status in ["DEFICIENT", "SUBMITTED"]:
                if o.status == "SUBMITTED":
                    holding = "WAITING_ON_AICTE"
                    resp = "Compliance Review Officer"
                    blocker = "Proof of compliance uploaded; awaiting official verification."
                    next_action = "Review uploaded evidence and commit verification determination."
                else:
                    holding = "WAITING_ON_INSTITUTION"
                    resp = "Institution Administrator"
                    blocker = f"Undertaking '{o.title}' is {abs(days_rem)} days overdue." if is_overdue else "Obligation deficient; resubmission needed."
                    next_action = "Upload valid evidence document conforming to APH norms."

                items.append(BottleneckItem(
                    id=o.id,
                    case_type="COMPLIANCE",
                    reference_no=o.title[:30],
                    institution_name=o.institution.name if o.institution else "N/A",
                    region_name=o.institution.region.name if o.institution and o.institution.region else "N/A",
                    current_status=o.status,
                    holding_side=holding,
                    responsible_party=resp,
                    age_days=max(0, -days_rem) if is_overdue else 0,
                    deadline_days_remaining=days_rem,
                    is_overdue=is_overdue,
                    escalation_state="CRITICAL_ESCALATION" if is_overdue and abs(days_rem) >= 7 else "SLA_BREACH",
                    blocker_reason=blocker,
                    next_permissible_action=next_action
                ))

        # Sort items by overdue first, then age descending
        items.sort(key=lambda x: (not x.is_overdue, -x.age_days))

        total_exceptions = len(items)
        waiting_inst = sum(1 for i in items if i.holding_side == "WAITING_ON_INSTITUTION")
        waiting_aicte = sum(1 for i in items if i.holding_side == "WAITING_ON_AICTE")
        overdue_cnt = sum(1 for i in items if i.is_overdue)
        crit_esc = sum(1 for i in items if i.escalation_state == "CRITICAL_ESCALATION")

        return BottleneckSummary(
            total_exceptions=total_exceptions,
            waiting_on_institution=waiting_inst,
            waiting_on_aicte=waiting_aicte,
            overdue_count=overdue_cnt,
            critical_escalations=crit_esc,
            items=items
        )
