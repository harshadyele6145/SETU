from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict
from jose import jwt, JWTError
import bcrypt
from enum import Enum
from backend.app.core.config import settings


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
    password_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


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
