from datetime import date, datetime, timezone
from typing import Optional
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.models.document import DocumentRegistry
from backend.app.models.institution import Institution
from backend.app.models.user import User
from backend.app.core.security import UserRole
from backend.app.core.storage import storage_service
from backend.app.services.auth_service import enforce_institution_scope
from backend.app.services.audit_service import audit_service


class DocumentService:
    @classmethod
    async def register_document(
        cls,
        db: Session,
        institution_id: str,
        document_category: str,
        title: str,
        issue_date: date,
        expiry_date: date,
        upload_file: UploadFile,
        application_id: Optional[str],
        actor: User
    ) -> DocumentRegistry:
        enforce_institution_scope(actor, institution_id)

        inst = db.get(Institution, institution_id)
        if not inst:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

        rel_path, sha256_hash, file_size, content_type = await storage_service.save_upload(upload_file)

        doc = DocumentRegistry(
            institution_id=institution_id,
            application_id=application_id,
            document_category=document_category,
            title=title,
            issue_date=issue_date,
            expiry_date=expiry_date,
            current_version=1,
            status="VALID",
            file_path=rel_path,
            file_size=file_size,
            mime_type=content_type,
            sha256_hash=sha256_hash,
            verified_by_id=actor.id if actor.role != UserRole.INST_ADMIN.value else None,
            verified_at=datetime.now(timezone.utc) if actor.role != UserRole.INST_ADMIN.value else None
        )
        db.add(doc)
        db.flush()

        audit_service.record_event(
            db=db,
            actor_role=actor.role,
            action="DOCUMENT_REGISTERED",
            entity_type="DOCUMENT",
            entity_id=doc.id,
            actor_id=actor.id,
            new_state="VALID",
            details={
                "category": document_category,
                "title": title,
                "expiry_date": expiry_date.isoformat(),
                "sha256": sha256_hash
            }
        )

        db.commit()
        db.refresh(doc)
        return doc

    @classmethod
    async def renew_document(
        cls,
        db: Session,
        old_document_id: str,
        issue_date: date,
        expiry_date: date,
        upload_file: UploadFile,
        actor: User
    ) -> DocumentRegistry:
        old_doc = db.get(DocumentRegistry, old_document_id)
        if not old_doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Previous document record not found")

        enforce_institution_scope(actor, old_doc.institution_id)

        rel_path, sha256_hash, file_size, content_type = await storage_service.save_upload(upload_file)

        # Invariant: Uploading a renewal does NOT immediately make the document VALID.
        # It enters RENEWAL_SUBMITTED awaiting authorized review.
        new_doc = DocumentRegistry(
            institution_id=old_doc.institution_id,
            application_id=old_doc.application_id,
            document_category=old_doc.document_category,
            title=old_doc.title,
            issue_date=issue_date,
            expiry_date=expiry_date,
            current_version=old_doc.current_version + 1,
            status="RENEWAL_SUBMITTED",
            file_path=rel_path,
            file_size=file_size,
            mime_type=content_type,
            sha256_hash=sha256_hash,
            previous_document_id=old_doc.id
        )
        db.add(new_doc)
        db.flush()

        # Mark old document as SUPERSEDED
        prev_old_status = old_doc.status
        old_doc.status = "SUPERSEDED"

        audit_service.record_event(
            db=db,
            actor_role=actor.role,
            action="DOCUMENT_RENEWAL_SUBMITTED",
            entity_type="DOCUMENT",
            entity_id=new_doc.id,
            actor_id=actor.id,
            previous_state=prev_old_status,
            new_state="RENEWAL_SUBMITTED",
            details={
                "version": new_doc.current_version,
                "previous_doc_id": old_doc.id,
                "new_expiry": expiry_date.isoformat(),
                "sha256": sha256_hash
            }
        )

        db.commit()
        db.refresh(new_doc)
        return new_doc

    @classmethod
    def verify_document(
        cls,
        db: Session,
        document_id: str,
        is_verified: bool,
        comments: Optional[str],
        reviewer: User
    ) -> DocumentRegistry:
        allowed_roles = (
            UserRole.RO_OFFICER.value,
            UserRole.BO_OFFICER.value,
            UserRole.COMP_REVIEW.value,
            UserRole.COMP_AUTH.value
        )
        if reviewer.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Unauthorized: Role {reviewer.role} cannot verify institutional documents."
            )

        doc = db.get(DocumentRegistry, document_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document record not found")

        prev_status = doc.status
        now = datetime.now(timezone.utc)

        if is_verified:
            doc.status = "VALID"
            doc.verified_by_id = reviewer.id
            doc.verified_at = now
        else:
            doc.status = "DEFICIENT"
            doc.verified_by_id = reviewer.id
            doc.verified_at = now

        audit_service.record_event(
            db=db,
            actor_role=reviewer.role,
            action="DOCUMENT_VERIFIED" if is_verified else "DOCUMENT_MARKED_DEFICIENT",
            entity_type="DOCUMENT",
            entity_id=doc.id,
            actor_id=reviewer.id,
            previous_state=prev_status,
            new_state=doc.status,
            details={"is_verified": is_verified, "comments": comments}
        )

        db.commit()
        db.refresh(doc)
        return doc

    @classmethod
    def get_protected_file_path(cls, db: Session, document_id: str, actor: User) -> str:
        doc = db.get(DocumentRegistry, document_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document record not found")

        # Authorization check: Institution users can only download documents of their own institution
        if actor.role == UserRole.INST_ADMIN.value:
            enforce_institution_scope(actor, doc.institution_id)

        return storage_service.get_absolute_path(doc.file_path)


document_service = DocumentService()
