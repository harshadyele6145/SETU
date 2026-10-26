from datetime import date, datetime, timezone
from typing import Optional, List
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.models.compliance import ComplianceObligation, ComplianceEvidence
from backend.app.models.institution import Institution
from backend.app.models.user import User
from backend.app.core.security import UserRole, is_role_in, normalize_role
from backend.app.core.storage import storage_service
from backend.app.services.auth_service import enforce_institution_scope
from backend.app.services.audit_service import audit_service


class ComplianceService:
    @classmethod
    def create_obligation(
        cls,
        db: Session,
        institution_id: str,
        category: str,
        title: str,
        description: str,
        due_date: date,
        condition_source: str,
        responsible_person: Optional[str],
        application_id: Optional[str],
        actor: User
    ) -> ComplianceObligation:
        inst = db.get(Institution, institution_id)
        if not inst:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

        obligation = ComplianceObligation(
            institution_id=institution_id,
            application_id=application_id,
            category=category,
            title=title,
            description=description,
            condition_source=condition_source,
            due_date=due_date,
            status="UPCOMING",
            responsible_person=responsible_person
        )
        db.add(obligation)
        db.flush()

        audit_service.record_event(
            db=db,
            actor_role=actor.role,
            action="COMPLIANCE_OBLIGATION_CREATED",
            entity_type="COMPLIANCE_OBLIGATION",
            entity_id=obligation.id,
            actor_id=actor.id,
            new_state="UPCOMING",
            details={"title": title, "due_date": due_date.isoformat()}
        )

        db.commit()
        db.refresh(obligation)
        return obligation

    @classmethod
    async def submit_evidence(
        cls,
        db: Session,
        obligation_id: str,
        upload_file: UploadFile,
        notes: Optional[str],
        actor: User
    ) -> ComplianceEvidence:
        obligation = db.get(ComplianceObligation, obligation_id)
        if not obligation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance obligation not found")

        # Invariant INV-03: Terminal Decision Immutability
        if obligation.application and obligation.application.status in ("APPROVED", "REJECTED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Statutory Invariant Violation (INV-03): Cannot submit compliance evidence for an application in terminal state '{obligation.application.status}'."
            )

        enforce_institution_scope(actor, obligation.institution_id)

        # Save file to protected storage and compute SHA-256 hash
        rel_path, sha256_hash, file_size, content_type = await storage_service.save_upload(upload_file)

        # Invariant INV-01: Uploaded evidence enters SUBMITTED, NEVER automatically VERIFIED
        evidence = ComplianceEvidence(
            obligation_id=obligation.id,
            institution_id=obligation.institution_id,
            file_name=upload_file.filename or "evidence_document",
            file_path=rel_path,
            file_size=file_size,
            mime_type=content_type,
            sha256_hash=sha256_hash,
            notes=notes,
            submitted_by_id=actor.id,
            submission_date=datetime.now(timezone.utc),
            verification_status="SUBMITTED"
        )
        db.add(evidence)
        db.flush()

        # Update obligation status
        prev_status = obligation.status
        obligation.status = "SUBMITTED"

        audit_service.record_event(
            db=db,
            actor_role=actor.role,
            action="COMPLIANCE_EVIDENCE_SUBMITTED",
            entity_type="COMPLIANCE_EVIDENCE",
            entity_id=evidence.id,
            actor_id=actor.id,
            previous_state=prev_status,
            new_state="SUBMITTED",
            details={
                "file_name": evidence.file_name,
                "sha256": sha256_hash,
                "obligation_title": obligation.title
            }
        )

        db.commit()
        db.refresh(evidence)
        return evidence

    @classmethod
    def verify_evidence(
        cls,
        db: Session,
        evidence_id: str,
        is_approved: bool,
        review_comments: str,
        reviewer: User
    ) -> ComplianceEvidence:
        allowed_roles = (
            UserRole.COMP_REVIEW.value,
            UserRole.COMP_REV.value,
            UserRole.RO_OFFICER.value,
            UserRole.REGIONAL_DIR.value,
            UserRole.BO_OFFICER.value,
            UserRole.BUREAU_OFFICER.value,
            UserRole.COMP_AUTH.value,
            UserRole.SYS_ADMIN.value
        )
        if not is_role_in(reviewer.role, allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Unauthorized: Role {reviewer.role} cannot verify compliance evidence."
            )

        if not review_comments or not review_comments.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reviewer comments are mandatory for compliance verification outcomes."
            )

        evidence = db.get(ComplianceEvidence, evidence_id)
        if not evidence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence record not found")

        obligation = evidence.obligation
        # Invariant INV-03: Terminal Decision Immutability
        if obligation and obligation.application and obligation.application.status in ("APPROVED", "REJECTED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Statutory Invariant Violation (INV-03): Cannot verify compliance evidence for an application in terminal state '{obligation.application.status}'."
            )
        now = datetime.now(timezone.utc)

        prev_status = evidence.verification_status
        if is_approved:
            new_ev_status = "VERIFIED"
            evidence.verification_status = new_ev_status
            evidence.verified_by_id = reviewer.id
            evidence.verified_at = now
            evidence.rejection_reason = None

            obligation.status = "VERIFIED"
            obligation.reviewer_id = reviewer.id
            obligation.review_comments = review_comments
            obligation.closed_at = now
        else:
            new_ev_status = "DEFICIENT"
            evidence.verification_status = new_ev_status
            evidence.verified_by_id = reviewer.id
            evidence.verified_at = now
            evidence.rejection_reason = review_comments

            obligation.status = "DEFICIENT"
            obligation.reviewer_id = reviewer.id
            obligation.review_comments = review_comments

        audit_service.record_event(
            db=db,
            actor_role=reviewer.role,
            action="COMPLIANCE_EVIDENCE_VERIFIED" if is_approved else "COMPLIANCE_EVIDENCE_REJECTED",
            entity_type="COMPLIANCE_EVIDENCE",
            entity_id=evidence.id,
            actor_id=reviewer.id,
            previous_state=prev_status,
            new_state=new_ev_status,
            details={"is_approved": is_approved, "comments": review_comments}
        )

        db.commit()
        db.refresh(evidence)
        return evidence


compliance_service = ComplianceService()
