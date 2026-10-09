from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import require_roles
from app.db.database import get_db
from app.models.machine_maintenance import (
    MaintenanceStatus,
    MaintenanceType,
)
from app.models.user import User, UserRole
from app.schemas.machine_maintenance import (
    MachineMaintenanceCreate,
    MachineMaintenanceResponse,
    MachineMaintenanceStatusUpdate,
    MachineMaintenanceUpdate,
)
from app.services.machine_maintenance_service import (
    create_maintenance,
    delete_maintenance,
    get_maintenance,
    list_maintenance,
    update_maintenance,
    update_maintenance_status,
)


router = APIRouter(
    prefix="/machine-maintenance",
    tags=["Machine Maintenance"],
)


MANAGE_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.MAINTENANCE_ENGINEER,
    UserRole.PLANT_MANAGER,
)

VIEW_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.MAINTENANCE_ENGINEER,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
)


@router.post(
    "",
    response_model=MachineMaintenanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_machine_maintenance(
    data: MachineMaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    return create_maintenance(
        db,
        data,
        current_user.id,
    )


@router.get(
    "",
    response_model=list[MachineMaintenanceResponse],
)
def get_machine_maintenance(
    machine_id: int | None = Query(
        default=None,
        gt=0,
    ),
    maintenance_status: MaintenanceStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    return list_maintenance(
        db,
        machine_id=machine_id,
        maintenance_status=maintenance_status,
    )


@router.get(
    "/{maintenance_id}",
    response_model=MachineMaintenanceResponse,
)
def get_machine_maintenance_record(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    return get_maintenance(
        db,
        maintenance_id,
    )


@router.put(
    "/{maintenance_id}",
    response_model=MachineMaintenanceResponse,
)
def update_machine_maintenance(
    maintenance_id: int,
    data: MachineMaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    return update_maintenance(
        db,
        maintenance_id,
        data,
    )


@router.patch(
    "/{maintenance_id}/status",
    response_model=MachineMaintenanceResponse,
)
def update_machine_maintenance_status(
    maintenance_id: int,
    data: MachineMaintenanceStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    return update_maintenance_status(
        db,
        maintenance_id,
        data,
    )


@router.delete(
    "/{maintenance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_machine_maintenance(
    maintenance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    delete_maintenance(
        db,
        maintenance_id,
    )