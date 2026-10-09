from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth.dependencies import require_roles
from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    DashboardOverview,
    InventoryDashboard,
    MaintenanceDashboard,
    ProductionDashboard,
    QualityDashboard,
)
from app.services.dashboard_service import (
    get_dashboard_overview,
    get_inventory_dashboard,
    get_maintenance_dashboard,
    get_production_dashboard,
    get_quality_dashboard,
)


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


DASHBOARD_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.QUALITY_MANAGER,
    UserRole.MAINTENANCE_ENGINEER,
    UserRole.STORE_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
)


@router.get(
    "",
    response_model=DashboardOverview,
)
def dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*DASHBOARD_ROLES)
    ),
):
    return get_dashboard_overview(db)


@router.get(
    "/production",
    response_model=ProductionDashboard,
)
def production_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*DASHBOARD_ROLES)
    ),
):
    return get_production_dashboard(db)


@router.get(
    "/quality",
    response_model=QualityDashboard,
)
def quality_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*DASHBOARD_ROLES)
    ),
):
    return get_quality_dashboard(db)


@router.get(
    "/maintenance",
    response_model=MaintenanceDashboard,
)
def maintenance_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*DASHBOARD_ROLES)
    ),
):
    return get_maintenance_dashboard(db)


@router.get(
    "/inventory",
    response_model=InventoryDashboard,
)
def inventory_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*DASHBOARD_ROLES)
    ),
):
    return get_inventory_dashboard(db)