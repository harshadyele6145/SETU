import os
from typing import Dict, Any, List
from fastapi import APIRouter, status, Response, Depends
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import check_database_health, get_db
from backend.app.schemas.health import HealthResponse
from backend.app.models.job import JobExecution
from backend.app.models.base import utc_now

router = APIRouter(tags=["Health & System Status"])


@router.get("/health", response_model=HealthResponse)
def health_probe(response: Response):
    db_ok = check_database_health()
    storage_ok = os.path.exists(settings.STORAGE_DIR) and os.access(settings.STORAGE_DIR, os.W_OK)

    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="healthy" if db_ok and storage_ok else "degraded",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database_connected=db_ok,
        details={
            "storage_writable": storage_ok,
            "demo_mode": settings.DEMO_MODE,
            "timezone": settings.DEFAULT_TIMEZONE
        }
    )


@router.get("/health/live")
def liveness_probe():
    """Kubernetes / Container Liveness Probe."""
    return {
        "status": "alive",
        "timestamp": utc_now().isoformat(),
        "version": settings.VERSION
    }


@router.get("/ready", response_model=HealthResponse)
def readiness_probe(response: Response):
    return health_probe(response)


@router.get("/health/ready")
def k8s_readiness_probe(response: Response):
    """Kubernetes / Container Readiness Probe."""
    db_ok = check_database_health()
    storage_ok = os.path.exists(settings.STORAGE_DIR) and os.access(settings.STORAGE_DIR, os.W_OK)

    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "degraded",
            "database_connected": False,
            "storage_writable": storage_ok,
            "ready": False
        }

    return {
        "status": "healthy",
        "database_connected": True,
        "storage_writable": storage_ok,
        "ready": True,
        "environment": settings.ENVIRONMENT,
        "timestamp": utc_now().isoformat()
    }


@router.get("/api/health", response_model=HealthResponse)
def api_health_probe(response: Response):
    return health_probe(response)


@router.get("/health/jobs")
def get_job_ledger(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Returns persistent background job execution ledger entries."""
    from sqlalchemy import desc
    jobs = db.query(JobExecution).order_by(desc(JobExecution.started_at)).limit(limit).all()
    return [
        {
            "id": j.id,
            "job_name": j.job_name,
            "status": j.status,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            "items_processed": j.items_processed,
            "execution_time_ms": j.execution_time_ms,
            "error_message": j.error_message
        }
        for j in jobs
    ]
