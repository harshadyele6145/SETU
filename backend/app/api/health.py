import os
from fastapi import APIRouter, status, Response
from backend.app.core.config import settings
from backend.app.core.database import check_database_health
from backend.app.schemas.health import HealthResponse

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


@router.get("/ready", response_model=HealthResponse)
def readiness_probe(response: Response):
    return health_probe(response)


@router.get("/api/health", response_model=HealthResponse)
def api_health_probe(response: Response):
    return health_probe(response)
