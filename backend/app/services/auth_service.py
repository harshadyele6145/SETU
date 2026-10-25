from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token, UserRole
from backend.app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    stmt = select(User).where(User.id == user_id, User.is_active == True)
    user = db.execute(stmt).scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


def require_roles(*allowed_roles: str):
    """
    Dependency factory checking if the authenticated user has one of the allowed roles.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires one of roles {[r for r in allowed_roles]}. Current role: {current_user.role}"
            )
        return current_user
    return role_checker


def enforce_institution_scope(current_user: User, institution_id: str) -> None:
    """
    Backend-enforced boundary: If the user is an Institution Administrator,
    they can strictly and only access/mutate records belonging to their assigned institution.
    """
    if current_user.role == UserRole.INST_ADMIN.value:
        if str(current_user.institution_id) != str(institution_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security violation: You are not authorized to view or modify records of another institution."
            )


def enforce_region_scope(current_user: User, region_id: str) -> None:
    """
    Backend-enforced boundary: Regional Officers can only access/act upon cases
    belonging to their designated geographic region.
    """
    if current_user.role == UserRole.RO_OFFICER.value:
        if str(current_user.region_id) != str(region_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security violation: Regional Officer cannot access or modify cases outside their designated Region."
            )


def require_statutory_authority(current_user: User) -> None:
    """
    Statutory Safeguard: Only Competent Authority (COMP_AUTH) can issue final statutory approvals/rejections.
    """
    if current_user.role != UserRole.COMP_AUTH.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Regulatory Safeguard: Final statutory approval or rejection decisions are strictly reserved for the Competent Authority."
        )
