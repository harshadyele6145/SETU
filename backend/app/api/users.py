from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.institution import Institution
from backend.app.models.region import Region
from backend.app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/users", tags=["User & Access Scope Administration"])


class UserItemResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    region_id: Optional[str] = None
    region_name: Optional[str] = None
    statutory_authority: bool


class RoleDefinition(BaseModel):
    role_key: str
    title: str
    scope_level: str
    can_approve: bool
    can_verify_compliance: bool
    can_assign_evc: bool
    description: str


ROLE_DEFINITIONS = [
    {
        "role_key": "INST_ADMIN",
        "title": "Institution Administrator",
        "scope_level": "Strictly Own Institution",
        "can_approve": False,
        "can_verify_compliance": False,
        "can_assign_evc": False,
        "description": "Submits applications, uploads mandatory undertaking evidence, registers regulatory documents, and responds to deficiency notices."
    },
    {
        "role_key": "RO_OFFICER",
        "title": "Regional Office Officer",
        "scope_level": "Regional Boundary (North/West)",
        "can_approve": False,
        "can_verify_compliance": False,
        "can_assign_evc": False,
        "description": "Performs initial scrutiny, issues deficiency returns, reviews resubmissions, and recommends applications for EVC or bureau consideration."
    },
    {
        "role_key": "REGIONAL_DIR",
        "title": "Regional Director",
        "scope_level": "Regional Boundary",
        "can_approve": False,
        "can_verify_compliance": False,
        "can_assign_evc": True,
        "description": "Supervises regional workflows, authorizes scrutiny reports, and monitors regional compliance pendency."
    },
    {
        "role_key": "BUREAU_OFFICER",
        "title": "AICTE Bureau Officer",
        "scope_level": "National / Cross-Regional",
        "can_approve": False,
        "can_verify_compliance": False,
        "can_assign_evc": False,
        "description": "Conducts national policy evaluations, routes complex cases to committees, and oversees operational bottleneck cockpits."
    },
    {
        "role_key": "EVC_COORD",
        "title": "EVC Coordinator",
        "scope_level": "Regional / Multi-Regional",
        "can_approve": False,
        "can_verify_compliance": False,
        "can_assign_evc": True,
        "description": "Schedules Expert Visit Committees, assigns qualified experts from roster, handles delay justifications, and collates field inspection reports."
    },
    {
        "role_key": "COMMITTEE_MBR",
        "title": "Expert Committee Member",
        "scope_level": "Assigned Visits Only",
        "can_approve": False,
        "can_verify_compliance": False,
        "can_assign_evc": False,
        "description": "Reviews assigned inspection files, submits on-site visit findings, flags infrastructure deficiencies, and signs off on verification reports."
    },
    {
        "role_key": "COMP_REV",
        "title": "Compliance Reviewer",
        "scope_level": "National / Regional",
        "can_approve": False,
        "can_verify_compliance": True,
        "can_assign_evc": False,
        "description": "Validates condition-precedent undertakings, accepts or rejects institutional compliance proof, and assesses lease / NOC renewals."
    },
    {
        "role_key": "COMP_AUTH",
        "title": "Competent Authority (Council)",
        "scope_level": "National (Sole Statutory Decision-Maker)",
        "can_approve": True,
        "can_verify_compliance": True,
        "can_assign_evc": True,
        "description": "Holds exclusive legal authority under the AICTE Act to grant final Approval, Approval with Conditions, or Statutory Rejection."
    }
]


@router.get("", response_model=List[UserItemResponse])
def get_users_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Apply server-side RBAC scoping for user listing:
    # INST_ADMIN can only see users of their own institution
    # RO_OFFICER and REGIONAL_DIR can see users within their region
    # Others (BUREAU_OFFICER, COMP_REV, COMP_AUTH, EVC_COORD) see all users
    stmt = select(User)
    if current_user.role == "INST_ADMIN":
        stmt = stmt.where(User.institution_id == current_user.institution_id)
    elif current_user.role in ("RO_OFFICER", "REGIONAL_DIR"):
        stmt = stmt.where(
            (User.region_id == current_user.region_id) | 
            (User.institution.has(Institution.region_id == current_user.region_id))
        )

    users = db.execute(stmt).scalars().all()
    
    # Pre-fetch lookup maps
    insts = {i.id: i.name for i in db.execute(select(Institution)).scalars().all()}
    regs = {r.id: r.name for r in db.execute(select(Region)).scalars().all()}

    results = []
    for u in users:
        inst_name = insts.get(u.institution_id) if u.institution_id else None
        reg_name = regs.get(u.region_id) if u.region_id else None
        
        # If institution has region and user doesn't have direct region
        if not reg_name and u.institution_id:
            inst_obj = db.execute(select(Institution).where(Institution.id == u.institution_id)).scalar_one_or_none()
            if inst_obj and inst_obj.region_id:
                reg_name = regs.get(inst_obj.region_id)

        results.append(
            UserItemResponse(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                role=u.role,
                is_active=u.is_active,
                institution_id=u.institution_id,
                institution_name=inst_name,
                region_id=u.region_id,
                region_name=reg_name,
                statutory_authority=(u.role == "COMP_AUTH")
            )
        )
    return results


@router.get("/roles", response_model=List[RoleDefinition])
def get_role_definitions(current_user: User = Depends(get_current_user)):
    return ROLE_DEFINITIONS
