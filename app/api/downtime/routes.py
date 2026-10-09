from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import require_roles
from app.db.database import get_db
from app.models.downtime import DowntimeStatus
from app.models.user import UserRole
from app.schemas.downtime import (
    DowntimeCreate,
    DowntimeResponse,
    DowntimeStatusUpdate,
    DowntimeUpdate,
)
from app.services.downtime_service import (
    create_downtime,
    delete_downtime,
    get_downtime,
    list_downtimes,
    update_downtime,
    update_downtime_status,
)


router = APIRouter(
    prefix="/downtime",
    tags=["Downtime"],
)


MANAGE_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.MAINTENANCE_ENGINEER,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
)


VIEW_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.MAINTENANCE_ENGINEER,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
    UserRole.QUALITY_MANAGER,
)


@router.post(
    "",
    response_model=DowntimeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: DowntimeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(*MANAGE_ROLES)),
):
    return create_downtime(db, data)


@router.get(
    "",
    response_model=list[DowntimeResponse],
)
def list_all(
    machine_id: int | None = Query(default=None, gt=0),
    status_value: DowntimeStatus | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(*VIEW_ROLES)),
):
    return list_downtimes(
        db,
        machine_id=machine_id,
        status_value=status_value,
    )


@router.get(
    "/{downtime_id}",
    response_model=DowntimeResponse,
)
def get_one(
    downtime_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(*VIEW_ROLES)),
):
    return get_downtime(db, downtime_id)


@router.put(
    "/{downtime_id}",
    response_model=DowntimeResponse,
)
def update(
    downtime_id: int,
    data: DowntimeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(*MANAGE_ROLES)),
):
    return update_downtime(
        db,
        downtime_id,
        data,
    )


@router.patch(
    "/{downtime_id}/status",
    response_model=DowntimeResponse,
)
def update_status(
    downtime_id: int,
    data: DowntimeStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(*MANAGE_ROLES)),
):
    return update_downtime_status(
        db,
        downtime_id,
        data,
    )


@router.delete(
    "/{downtime_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    downtime_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(*MANAGE_ROLES)),
):
    delete_downtime(db, downtime_id)