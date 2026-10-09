from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.reports import (
    DowntimeReport,
    InventoryReport,
    MaintenanceReport,
    ProductionApprovalReport,
    ProductionReport,
    QualityReport,
    ReportsOverview,
)
from app.services.reports_service import (
    get_downtime_report,
    get_inventory_report,
    get_maintenance_report,
    get_production_approval_report,
    get_production_report,
    get_quality_report,
    get_reports_overview,
)


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


REPORT_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.QUALITY_MANAGER,
    UserRole.MAINTENANCE_ENGINEER,
    UserRole.STORE_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
}


def check_report_access(
    current_user: User,
) -> User:
    if current_user.role not in REPORT_ROLES:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return current_user


@router.get(
    "",
    response_model=ReportsOverview,
)
def reports_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_report_access(current_user)

    return get_reports_overview(db)


@router.get(
    "/production",
    response_model=ProductionReport,
)
def production_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_report_access(current_user)

    return get_production_report(db)


@router.get(
    "/quality",
    response_model=QualityReport,
)
def quality_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_report_access(current_user)

    return get_quality_report(db)


@router.get(
    "/inventory",
    response_model=InventoryReport,
)
def inventory_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_report_access(current_user)

    return get_inventory_report(db)


@router.get(
    "/maintenance",
    response_model=MaintenanceReport,
)
def maintenance_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_report_access(current_user)

    return get_maintenance_report(db)


@router.get(
    "/downtime",
    response_model=DowntimeReport,
)
def downtime_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_report_access(current_user)

    return get_downtime_report(db)


@router.get(
    "/production-approvals",
    response_model=ProductionApprovalReport,
)
def production_approval_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_report_access(current_user)

    return get_production_approval_report(db)