from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict
from jose import jwt, JWTError
from passlib.context import CryptContext
from enum import Enum
from backend.app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, Enum):
    INST_ADMIN = "INST_ADMIN"        # Institution Administrator
    RO_OFFICER = "RO_OFFICER"        # Regional Officer
    BO_OFFICER = "BO_OFFICER"        # Bureau Officer
    EVC_COORD = "EVC_COORD"          # EVC Coordinator
    COMM_MEMBER = "COMM_MEMBER"      # Committee Member
    COMP_REVIEW = "COMP_REVIEW"      # Compliance Reviewer
    COMP_AUTH = "COMP_AUTH"          # Competent Authority
    SYS_ADMIN = "SYS_ADMIN"          # System Administrator


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
