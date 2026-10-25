from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.auth_service import get_current_user
from backend.app.models.user import User
from backend.app.services.dashboard_service import DashboardService


router = APIRouter(prefix="/api/dashboard", tags=["Operational Dashboard"])


@router.get("/stats")
def get_dashboard_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns dynamically computed real-time statistics from the database.
    Zero hardcoded values; fully scoped to current user.
    """
    return DashboardService.get_dashboard_metrics(db=db, user=current_user)
