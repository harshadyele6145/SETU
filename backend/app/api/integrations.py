import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.services.auth_service import get_current_user
from backend.app.adapters.external_portal import mock_portal_adapter, SyncResult, IntegrationHealthStatus, ExternalInstitutionProfile
from backend.app.services.audit_service import audit_service

router = APIRouter(prefix="/api/integrations", tags=["AICTE External Portal Integration"])

# In-memory sync log for prototype demonstration telemetry
SYNC_HISTORY: List[Dict[str, Any]] = [
    {
        "id": "SYNC-LOG-001",
        "timestamp": "2026-10-25T10:15:30Z",
        "action": "PUSH_DECISION",
        "application_no": "AICTE/WRO/2026/001",
        "decision": "APPROVED",
        "status_code": 200,
        "success": True,
        "external_ref": "AICTE-SYNC-1729851330",
        "message": "Decision successfully synchronized with AICTE national database."
    },
    {
        "id": "SYNC-LOG-002",
        "timestamp": "2026-10-25T11:00:15Z",
        "action": "FETCH_PROFILE",
        "aicte_id": "1-3324567891",
        "decision": "-",
        "status_code": 200,
        "success": True,
        "external_ref": "PROFILE-CACHE-09",
        "message": "Institutional master data retrieved."
    }
]


class ToggleFailureRequest(BaseModel):
    simulate_failure: bool


class PushDecisionRequest(BaseModel):
    application_no: str
    decision: str
    comments: Optional[str] = "Statutory decision synchronization from SETU workflow engine."


@router.get("/status")
def get_adapter_status(current_user: User = Depends(get_current_user)):
    health = mock_portal_adapter.check_health()
    return {
        "health": health.model_dump(),
        "recent_syncs": list(reversed(SYNC_HISTORY[-10:])),
        "total_sync_count": len(SYNC_HISTORY) + mock_portal_adapter.call_count
    }


@router.post("/toggle-failure")
def toggle_adapter_failure(
    payload: ToggleFailureRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    mock_portal_adapter.set_simulate_failure(payload.simulate_failure)
    
    audit_service.record_event(
        db=db,
        actor_role=current_user.role,
        action="ADAPTER_FAILURE_SIMULATION_TOGGLED",
        entity_type="INTEGRATION_ADAPTER",
        entity_id="MockPortalAdapter",
        actor_id=current_user.id,
        new_state=f"FAILURE_MODE_{payload.simulate_failure}",
        details={"simulate_failure": payload.simulate_failure, "toggled_by": current_user.email}
    )
    db.commit()

    return {
        "message": f"Simulated failure mode set to {payload.simulate_failure}",
        "simulate_failure": payload.simulate_failure
    }


@router.post("/test-push", response_model=SyncResult)
def test_push_decision(
    payload: PushDecisionRequest,
    current_user: User = Depends(get_current_user)
):
    result = mock_portal_adapter.push_approval_decision(
        application_no=payload.application_no,
        decision=payload.decision,
        comments=payload.comments
    )
    
    # Record in telemetry
    log_entry = {
        "id": f"SYNC-LOG-{int(time.time()*1000) % 1000000:06d}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": "PUSH_DECISION",
        "application_no": payload.application_no,
        "decision": payload.decision,
        "status_code": result.status_code,
        "success": result.success,
        "external_ref": result.external_reference_id or "N/A",
        "message": result.message
    }
    SYNC_HISTORY.append(log_entry)
    
    return result


@router.get("/fetch-institution/{aicte_id}", response_model=ExternalInstitutionProfile)
def fetch_institution_profile(
    aicte_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        profile = mock_portal_adapter.fetch_institution_profile(aicte_id=aicte_id)
        
        log_entry = {
            "id": f"SYNC-LOG-{int(time.time()*1000) % 1000000:06d}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "action": "FETCH_PROFILE",
            "aicte_id": aicte_id,
            "decision": "-",
            "status_code": 200,
            "success": True,
            "external_ref": f"AIC-PROFILE-{aicte_id}",
            "message": "Successfully fetched from mock gateway."
        }
        SYNC_HISTORY.append(log_entry)
        return profile
    except ConnectionError as e:
        log_entry = {
            "id": f"SYNC-LOG-{int(time.time()*1000) % 1000000:06d}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "action": "FETCH_PROFILE",
            "aicte_id": aicte_id,
            "decision": "-",
            "status_code": 503,
            "success": False,
            "external_ref": "FAILED",
            "message": str(e)
        }
        SYNC_HISTORY.append(log_entry)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@router.get("/prerequisites")
def get_integration_prerequisites(current_user: User = Depends(get_current_user)):
    return {
        "status": "PROTOTYPE_SIMULATION_ACTIVE",
        "disclaimer": "Live integration with production AICTE systems requires formal clearance, MoUs, and approved API keys. SETU uses an ExternalPortalAdapter boundary.",
        "prerequisites": [
            {
                "id": "PR-01",
                "title": "Confirmed Official AICTE Central APIs",
                "status": "PENDING_AICTE_SPEC",
                "description": "Standardized OpenAPI/REST/SOAP endpoints for National Council application registries."
            },
            {
                "id": "PR-02",
                "title": "Mutual TLS (mTLS) & NIC Gateway Credentials",
                "status": "GOVERNMENT_SECURITY_CLEARANCE",
                "description": "X.509 client certificates and secure VPN gateway access provided by National Informatics Centre (NIC)."
            },
            {
                "id": "PR-03",
                "title": "Idempotent Synchronous & Asynchronous Webhooks",
                "status": "ADAPTER_CONTRACT_DEFINED",
                "description": "SETU ExternalPortalAdapter defines strict SHA-256 idempotency keys preventing dual ingestion."
            },
            {
                "id": "PR-04",
                "title": "Automated Reconciliation Queue",
                "status": "IMPLEMENTED_IN_SETU",
                "description": "Outbox and retry scheduler buffers sync events during gateway downtimes and replays upon recovery."
            },
            {
                "id": "PR-05",
                "title": "Data Privacy & Data Sharing Governance",
                "status": "DPDP_ACT_COMPLIANT",
                "description": "Only authorized officer roles (Bureau Officer, Competent Authority) can trigger cross-system synchronization."
            }
        ]
    }
