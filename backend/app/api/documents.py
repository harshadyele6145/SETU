from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.models.document import DocumentRegistry
from backend.app.models.institution import Institution
from backend.app.models.evc import EVCVisit, EVCExpert
from backend.app.models.user import User
from backend.app.core.security import UserRole
from backend.app.schemas.document import DocumentResponse, DocumentVerifyRequest
from backend.app.services.auth_service import get_current_user, enforce_institution_scope
from backend.app.services.document_service import document_service
from backend.app.services.extraction_service import extraction_service

router = APIRouter(prefix="/api/documents", tags=["Document Registry & Renewals"])


def format_document_response(doc: DocumentRegistry) -> DocumentResponse:
    today = date.today()
    days_to_expiry = (doc.expiry_date - today).days

    return DocumentResponse(
        id=doc.id,
        institution_id=doc.institution_id,
        institution_name=doc.institution.name if doc.institution else None,
        application_id=doc.application_id,
        application_no=doc.application.application_no if doc.application else None,
        document_category=doc.document_category,
        title=doc.title,
        issue_date=doc.issue_date,
        expiry_date=doc.expiry_date,
        current_version=doc.current_version,
        status=doc.status,
        file_path=doc.file_path,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        sha256_hash=doc.sha256_hash,
        verified_by_name=doc.verified_by.full_name if doc.verified_by else None,
        verified_at=doc.verified_at,
        previous_document_id=doc.previous_document_id,
        days_to_expiry=days_to_expiry,
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    institution_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stmt = select(DocumentRegistry)

    # Server-enforced scope boundary
    if current_user.role == UserRole.INST_ADMIN.value:
        if not current_user.institution_id:
            return []
        stmt = stmt.where(DocumentRegistry.institution_id == current_user.institution_id)
    elif current_user.role in [UserRole.RO_OFFICER.value, UserRole.REGIONAL_DIR.value, UserRole.EVC_COORD.value]:
        if not current_user.region_id:
            return []
        stmt = stmt.join(Institution, DocumentRegistry.institution_id == Institution.id).where(
            Institution.region_id == current_user.region_id
        )
    elif current_user.role in [UserRole.COMMITTEE_MBR.value, UserRole.COMM_MEMBER.value]:
        assigned_app_ids = [
            row[0] for row in db.query(EVCVisit.application_id)
            .join(EVCExpert)
            .filter(EVCExpert.contact_email == current_user.email)
            .all()
        ]
        if not assigned_app_ids:
            return []
        stmt = stmt.where(DocumentRegistry.application_id.in_(assigned_app_ids))
    elif institution_id:
        stmt = stmt.where(DocumentRegistry.institution_id == institution_id)

    if category:
        stmt = stmt.where(DocumentRegistry.document_category == category)
    if status:
        stmt = stmt.where(DocumentRegistry.status == status)

    stmt = stmt.order_by(DocumentRegistry.expiry_date.asc())
    docs = db.execute(stmt).scalars().all()
    return [format_document_response(d) for d in docs]


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def register_document(
    institution_id: str = Form(...),
    document_category: str = Form(...),
    title: str = Form(...),
    issue_date: date = Form(...),
    expiry_date: date = Form(...),
    application_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == UserRole.INST_ADMIN.value:
        enforce_institution_scope(current_user, institution_id)

    doc = await document_service.register_document(
        db=db,
        institution_id=institution_id,
        document_category=document_category,
        title=title,
        issue_date=issue_date,
        expiry_date=expiry_date,
        upload_file=file,
        application_id=application_id,
        actor=current_user
    )
    return format_document_response(doc)


@router.post("/{id}/renew", response_model=DocumentResponse)
async def renew_document(
    id: str,
    issue_date: date = Form(...),
    expiry_date: date = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = await document_service.renew_document(
        db=db,
        old_document_id=id,
        issue_date=issue_date,
        expiry_date=expiry_date,
        upload_file=file,
        actor=current_user
    )
    return format_document_response(doc)


@router.post("/{id}/verify", response_model=DocumentResponse)
def verify_document(
    id: str,
    payload: DocumentVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = document_service.verify_document(
        db=db,
        document_id=id,
        is_verified=payload.is_verified,
        comments=payload.comments,
        reviewer=current_user
    )
    return format_document_response(doc)


@router.get("/{id}/download")
def download_protected_document(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enforces record-level access control before serving the physical file.
    """
    abs_path = document_service.get_protected_file_path(db, id, current_user)
    doc = db.get(DocumentRegistry, id)
    filename = f"{doc.document_category}_{doc.title}.pdf" if doc else "document.pdf"

    return FileResponse(
        path=abs_path,
        media_type=doc.mime_type if doc else "application/octet-stream",
        filename=filename
    )


@router.get("/{id}/extract")
def extract_and_analyze_document(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extracts text and regulatory metadata from an uploaded document,
    cross-referencing with registered metadata and detecting discrepancies.
    """
    abs_path = document_service.get_protected_file_path(db, id, current_user)
    doc = db.get(DocumentRegistry, id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    analysis = extraction_service.analyze_document(
        file_path=str(abs_path),
        registered_title=doc.title,
        registered_category=doc.document_category,
        registered_expiry=doc.expiry_date.isoformat() if doc.expiry_date else None
    )
    return analysis
