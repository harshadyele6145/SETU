import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import engine, Base, SessionLocal
from backend.app.models import *  # Import all models to register with Base
from backend.app.api.health import router as health_router
from backend.app.api.auth import router as auth_router
from backend.app.api.applications import router as applications_router
from backend.app.api.compliance import router as compliance_router
from backend.app.api.documents import router as documents_router
from backend.app.api.alerts import router as alerts_router
from backend.app.api.evc import router as evc_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.reports import router as reports_router
from backend.app.api.attention import router as attention_router
from backend.app.api.bottlenecks import router as bottlenecks_router
from backend.app.api.audit import router as audit_router
from backend.app.api.integrations import router as integrations_router
from backend.app.api.users import router as users_router
from backend.app.core.migrations import run_schema_migrations
from backend.app.middleware.observability import ObservabilityMiddleware
from backend.app.services.scheduler import scheduler_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    run_schema_migrations()
    
    # Check for missed background jobs on startup
    try:
        with SessionLocal() as db:
            scheduler_service.check_missed_jobs_and_recover(db)
    except Exception as e:
        import logging
        logging.getLogger("setu").warning(f"Initial job recovery check warning: {e}")

    # Start background scheduler
    scheduler_service.start()
    yield
    scheduler_service.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Unified Workflow, Compliance and Deadline Intelligence Platform for AICTE Approvals (SIH26262)",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Observability and Security Headers Middleware
app.add_middleware(ObservabilityMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include core routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(applications_router)
app.include_router(compliance_router)
app.include_router(documents_router)
app.include_router(alerts_router)
app.include_router(evc_router)
app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(attention_router)
app.include_router(bottlenecks_router)
app.include_router(audit_router)
app.include_router(integrations_router)
app.include_router(users_router)


@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/api/docs",
        "health_check": "/health"
    }
