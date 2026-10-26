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
from backend.app.schemas.attention import AttentionQueueItem, AttentionFactor


class AttentionService:
    @staticmethod
    def compute_attention_queue(db: Session, user: User) -> List[AttentionQueueItem]:
        """
        Explainable Attention Engine: Deterministic multi-factor scoring algorithm.
        Ranks applications by urgency and generates plain-English diagnostic explanations.
        Strictly scopes items by user role, institution, region, and committee assignment.
        """
        query = db.query(Application).filter(Application.status.notin_(["APPROVED", "REJECTED"]))

        # Apply Scoping
        if user.role == "INST_ADMIN":
            if not user.institution_id:
                return []
            query = query.filter(Application.institution_id == user.institution_id)
        elif user.role in ["RO_OFFICER", "REGIONAL_DIR", "EVC_COORD"]:
            if not user.region_id:
                return []
            query = query.filter(Application.region_id == user.region_id)
        elif user.role in ["COMM_MEMBER", "COMMITTEE_MBR"]:
            assigned_ids = [
                row[0]
                for row in db.query(EVCVisit.application_id)
                .join(EVCExpert, EVCExpert.visit_id == EVCVisit.id)
                .filter(EVCExpert.contact_email == user.email)
                .all()
            ]
            if not assigned_ids:
                return []
            query = query.filter(Application.id.in_(assigned_ids))

        apps = query.all()
        now = utc_now()
        queue = []

        for a in apps:
            factors: List[AttentionFactor] = []
            score = 0

            # 1. SLA Urgency / Overdue Breach (Weight: 40)
            stage_at = a.stage_entered_at if a.stage_entered_at.tzinfo else a.stage_entered_at.replace(tzinfo=timezone.utc)
            days_in_stage = max(0, (now - stage_at).days)
            sla_days = a.current_stage.sla_days if a.current_stage else 15

            days_to_deadline = sla_days - days_in_stage
            is_overdue = days_to_deadline < 0

            if is_overdue:
                overdue_days = abs(days_to_deadline)
                overdue_pts = min(40, 25 + (overdue_days * 2))
                score += overdue_pts
                factors.append(AttentionFactor(
                    factor_name="SLA_BREACH",
                    weight=40,
                    points_awarded=overdue_pts,
                    rationale=f"Application has exceeded stage SLA by {overdue_days} days (in state for {days_in_stage}d, limit is {sla_days}d)."
                ))
            elif days_to_deadline <= 2:
                score += 25
                factors.append(AttentionFactor(
                    factor_name="URGENT_SLA_WINDOW",
                    weight=40,
                    points_awarded=25,
                    rationale=f"Stage SLA deadline expires in {days_to_deadline} days."
                ))
            elif days_to_deadline <= 7:
                score += 15
                factors.append(AttentionFactor(
                    factor_name="APPROACHING_DEADLINE",
                    weight=40,
                    points_awarded=15,
                    rationale=f"Deadline approaching in {days_to_deadline} days."
                ))

            # 2. Return / Deficiency Cycles (Weight: 20)
            if a.return_count >= 2:
                score += 20
                factors.append(AttentionFactor(
                    factor_name="CHRONIC_DEFICIENCY_RETURNS",
                    weight=20,
                    points_awarded=20,
                    rationale=f"Application returned {a.return_count} times for repeated institutional deficiencies."
                ))
            elif a.return_count == 1:
                score += 10
                factors.append(AttentionFactor(
                    factor_name="PREVIOUS_DEFICIENCY_RETURN",
                    weight=20,
                    points_awarded=10,
                    rationale="Application was previously returned once for deficiency clarification."
                ))

            # 3. Linked Compliance Obligations (Weight: 20)
            linked_obs = db.query(ComplianceObligation).filter(
                ComplianceObligation.application_id == a.id,
                ComplianceObligation.status.in_(["OVERDUE", "DEFICIENT", "DUE_SOON"])
            ).all()

            if any(o.status == "OVERDUE" for o in linked_obs):
                score += 20
                factors.append(AttentionFactor(
                    factor_name="OVERDUE_COMPLIANCE_UNDERTAKING",
                    weight=20,
                    points_awarded=20,
                    rationale="One or more mandatory approval condition undertakings are past due."
                ))
            elif any(o.status == "DEFICIENT" for o in linked_obs):
                score += 15
                factors.append(AttentionFactor(
                    factor_name="DEFICIENT_COMPLIANCE_EVIDENCE",
                    weight=20,
                    points_awarded=15,
                    rationale="Compliance proof was formally rejected by reviewer as deficient."
                ))
            elif any(o.status == "DUE_SOON" for o in linked_obs):
                score += 8
                factors.append(AttentionFactor(
                    factor_name="COMPLIANCE_DUE_SOON",
                    weight=20,
                    points_awarded=8,
                    rationale="Compliance obligation due in <= 7 days."
                ))

            # 4. Prescribed Documents / Lease Expiry (Weight: 15)
            expired_docs = db.query(DocumentRegistry).filter(
                DocumentRegistry.institution_id == a.institution_id,
                DocumentRegistry.status.in_(["EXPIRED", "EXPIRING_SOON"])
            ).all()

            if any(d.status == "EXPIRED" for d in expired_docs):
                score += 15
                factors.append(AttentionFactor(
                    factor_name="EXPIRED_PRESCRIBED_DOCUMENTS",
                    weight=15,
                    points_awarded=15,
                    rationale="Institution possesses expired registered lease deed or municipal fire NOC."
                ))
            elif any(d.status == "EXPIRING_SOON" for d in expired_docs):
                score += 8
                factors.append(AttentionFactor(
                    factor_name="DOCUMENTS_EXPIRING_SOON",
                    weight=15,
                    points_awarded=8,
                    rationale="Land or municipal safety approvals expiring within 30 days."
                ))

            # 5. EVC Visit Pending or Delayed (Weight: 15)
            evc_visit = db.query(EVCVisit).filter(EVCVisit.application_id == a.id).first()
            if a.status in ["EVC_SCHEDULED", "AWAITING_EVC", "EVC_QUEUE"]:
                if not evc_visit:
                    score += 15
                    factors.append(AttentionFactor(
                        factor_name="UNSCHEDULED_EVC_VISIT",
                        weight=15,
                        points_awarded=15,
                        rationale="Application is in EVC stage but physical inspection visit has not been scheduled."
                    ))
                elif evc_visit.delay_reason:
                    score += 12
                    factors.append(AttentionFactor(
                        factor_name="RESCHEDULED_EVC_VISIT",
                        weight=15,
                        points_awarded=12,
                        rationale=f"EVC visit was deferred: {evc_visit.delay_reason}"
                    ))

            # 6. Unassigned Case Officer (Weight: 10)
            if not a.assigned_officer_id and a.status not in ["DRAFT", "APPROVED", "REJECTED"]:
                score += 10
                factors.append(AttentionFactor(
                    factor_name="UNASSIGNED_OFFICER",
                    weight=10,
                    points_awarded=10,
                    rationale="Active application does not have a dedicated scrutiny officer assigned."
                ))

            # Determine Priority Tier
            if score >= 70:
                tier = "CRITICAL"
            elif score >= 45:
                tier = "HIGH"
            elif score >= 25:
                tier = "MEDIUM"
            else:
                tier = "LOW"

            # Determine Responsible Role & Prescriptive Action
            if a.status in ["DRAFT"]:
                role = "INST_ADMIN"
                rec_action = "Complete and formally submit application dossier to initiate AICTE processing."
                blocker = "Pending institutional submission."
            elif a.status in ["PENDING_CLARIFICATION", "SCRUTINY_DEFICIENT", "DEFICIENCY_COMMUNICATED"]:
                role = "INST_ADMIN"
                rec_action = "Upload requested deficiency clarifications and resubmit application within statutory window."
                blocker = "Deficiency notice issued by Scrutiny / EVC Committee."
            elif a.status == "SUBMITTED":
                role = "RO_OFFICER"
                rec_action = "Assign scrutiny officer and convene Document Scrutiny Committee."
                blocker = "Awaiting scrutiny commencement at Regional Office."
            elif a.status == "UNDER_SCRUTINY":
                role = "RO_OFFICER"
                rec_action = "Complete verification of physical land deeds, building plans, and statutory affidavits."
                blocker = "Under active scrutiny examination."
            elif a.status in ["SCRUTINY_RECOMMENDED", "AWAITING_EVC", "EVC_QUEUE"]:
                role = "EVC_COORD"
                rec_action = "Constitute 3-member visiting expert committee roster and confirm visit date."
                blocker = "EVC scheduling pending."
            elif a.status == "EVC_SCHEDULED":
                role = "COMMITTEE_MBR"
                rec_action = "Conduct on-site campus verification and upload signed inspection report."
                blocker = "Physical campus inspection in progress."
            elif a.status in ["EVC_COMPLETED", "EVC_REPORT_SUBMITTED"]:
                role = "RO_OFFICER"
                rec_action = "Review EVC inspection findings and formulate statutory recommendation."
                blocker = "EVC report under regional review."
            elif a.status in ["SAC_RECOMMENDED", "SHC_SCHEDULED", "DECISION_PENDING"]:
                role = "COMP_AUTH"
                rec_action = "Review Standing Appellate Committee recommendations and execute final statutory approval/rejection."
                blocker = "Pending Competent Authority final determination."
            else:
                role = "RO_OFFICER"
                rec_action = "Progress application to next workflow milestone."
                blocker = "Routine administrative review."

            # Construct human-readable diagnostic explanation
            top_factors = sorted(factors, key=lambda f: f.points_awarded, reverse=True)[:3]
            explanation = f"Priority score {score}/100. Primary operational drivers: " + "; ".join(
                f"{f.factor_name.replace('_', ' ')} (+{f.points_awarded} pts)" for f in top_factors
            ) if top_factors else "Standard in-process case progressing within normal SLA parameters."

            queue.append(AttentionQueueItem(
                application_id=a.id,
                application_no=a.application_no,
                institution_name=a.institution.name if a.institution else "N/A",
                region_name=a.region.name if a.region else "N/A",
                current_stage=a.current_stage.name if a.current_stage else a.status,
                priority_level=tier,
                composite_score=score,
                days_in_stage=days_in_stage,
                days_to_deadline=days_to_deadline,
                is_overdue=is_overdue,
                responsible_role=role,
                assigned_officer=a.assigned_officer.full_name if a.assigned_officer else None,
                blocking_dependency=blocker,
                recommended_action=rec_action,
                explanation=explanation,
                factors=factors
            ))

        # Sort queue by composite score descending
        return sorted(queue, key=lambda x: x.composite_score, reverse=True)
