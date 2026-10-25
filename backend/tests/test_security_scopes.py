import pytest
from fastapi import HTTPException
from backend.app.core.security import UserRole
from backend.app.models.user import User
from backend.app.services.auth_service import (
    enforce_institution_scope,
    enforce_region_scope,
    require_statutory_authority
)


def test_institution_scope_enforcement():
    inst_user = User(
        id="user-1",
        email="inst1@test.edu",
        role=UserRole.INST_ADMIN.value,
        institution_id="inst-alpha",
        full_name="Inst Admin Alpha"
    )

    # Permitted: accessing own institution
    enforce_institution_scope(inst_user, "inst-alpha")

    # Forbidden: attempting cross-institution access to inst-beta
    with pytest.raises(HTTPException) as exc_info:
        enforce_institution_scope(inst_user, "inst-beta")
    assert exc_info.value.status_code == 403
    assert "Security violation" in exc_info.value.detail


def test_region_scope_enforcement():
    ro_north_user = User(
        id="user-2",
        email="ro_north@test.gov",
        role=UserRole.RO_OFFICER.value,
        region_id="reg-north",
        full_name="RO North"
    )

    # Permitted: acting within North region
    enforce_region_scope(ro_north_user, "reg-north")

    # Forbidden: attempting action in Western region
    with pytest.raises(HTTPException) as exc_info:
        enforce_region_scope(ro_north_user, "reg-west")
    assert exc_info.value.status_code == 403
    assert "Regional Officer cannot access or modify cases outside their designated Region" in exc_info.value.detail


def test_statutory_authority_enforcement():
    # Non-statutory user (Regional Officer)
    ro_user = User(
        id="user-3",
        email="ro@test.gov",
        role=UserRole.RO_OFFICER.value,
        full_name="RO"
    )
    with pytest.raises(HTTPException) as exc_info:
        require_statutory_authority(ro_user)
    assert exc_info.value.status_code == 403
    assert "Regulatory Safeguard" in exc_info.value.detail

    # Non-statutory user (System Administrator)
    sys_admin = User(
        id="user-4",
        email="admin@test.gov",
        role=UserRole.SYS_ADMIN.value,
        full_name="Sys Admin"
    )
    with pytest.raises(HTTPException) as exc_info:
        require_statutory_authority(sys_admin)
    assert exc_info.value.status_code == 403

    # Authorized: Competent Authority
    comp_auth_user = User(
        id="user-5",
        email="ca@test.gov",
        role=UserRole.COMP_AUTH.value,
        full_name="Competent Authority"
    )
    # Permitted without raising exception
    require_statutory_authority(comp_auth_user)
