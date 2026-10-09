from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.shift import ShiftStatus, ShiftType
from app.models.user import UserRole
from app.schemas.shift import (
    ShiftCreate,
    ShiftMetricsResponse,
    ShiftOutputUpdate,
    ShiftResponse,
    ShiftStatusUpdate,
    ShiftUpdate,
    ShiftWorkerAssignment,
)
from app.services import shift_service

# Use the same authentication dependency used by
# the existing protected routers.
from app.api.auth.dependencies import (
    get_current_user,
    require_roles,
)


router = APIRouter(
    prefix="/shifts",
    tags=["Shifts"],
)


MANAGEMENT_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
]

SUPERVISION_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
]

VIEW_ROLES = [
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
    UserRole.WORKER,
]


@router.post(
    "",
    response_model=ShiftResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_shift(
    data: ShiftCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        return shift_service.create_shift(
            db,
            data,
            current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[ShiftResponse],
)
def list_shifts(
    shift_type: ShiftType | None = None,
    shift_date: date | None = None,
    production_line_id: int | None = Query(
        default=None,
        gt=0,
    ),
    shift_status: ShiftStatus | None = None,
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    return shift_service.list_shifts(
        db,
        shift_type=shift_type,
        shift_date=shift_date,
        production_line_id=production_line_id,
        status=shift_status,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{shift_id}",
    response_model=ShiftResponse,
)
def get_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    try:
        return shift_service.get_shift(
            db,
            shift_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.put(
    "/{shift_id}",
    response_model=ShiftResponse,
)
def update_shift(
    shift_id: int,
    data: ShiftUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        return shift_service.update_shift(
            db,
            shift_id,
            data,
        )
    except ValueError as exc:
        message = str(exc)

        if message == "Shift not found":
            raise HTTPException(
                status_code=404,
                detail=message,
            )

        raise HTTPException(
            status_code=400,
            detail=message,
        )


@router.patch(
    "/{shift_id}/status",
    response_model=ShiftResponse,
)
def update_shift_status(
    shift_id: int,
    data: ShiftStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*SUPERVISION_ROLES)
    ),
):
    try:
        return shift_service.update_shift_status(
            db,
            shift_id,
            data.status,
        )
    except ValueError as exc:
        message = str(exc)

        if message == "Shift not found":
            raise HTTPException(
                status_code=404,
                detail=message,
            )

        raise HTTPException(
            status_code=400,
            detail=message,
        )


@router.patch(
    "/{shift_id}/output",
    response_model=ShiftResponse,
)
def update_shift_output(
    shift_id: int,
    data: ShiftOutputUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*SUPERVISION_ROLES)
    ),
):
    try:
        return shift_service.update_shift_output(
            db,
            shift_id,
            data,
        )
    except ValueError as exc:
        message = str(exc)

        if message == "Shift not found":
            raise HTTPException(
                status_code=404,
                detail=message,
            )

        raise HTTPException(
            status_code=400,
            detail=message,
        )


@router.get(
    "/{shift_id}/metrics",
    response_model=ShiftMetricsResponse,
)
def get_shift_metrics(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    try:
        return shift_service.get_shift_metrics(
            db,
            shift_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.post(
    "/{shift_id}/workers",
    response_model=ShiftResponse,
)
def assign_worker(
    shift_id: int,
    data: ShiftWorkerAssignment,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*SUPERVISION_ROLES)
    ),
):
    try:
        shift_service.assign_worker(
            db,
            shift_id,
            data.worker_id,
        )

        return shift_service.get_shift(
            db,
            shift_id,
        )

    except ValueError as exc:
        message = str(exc)

        if message in {
            "Shift not found",
            "Worker not found",
        }:
            raise HTTPException(
                status_code=404,
                detail=message,
            )

        raise HTTPException(
            status_code=400,
            detail=message,
        )


@router.get(
    "/{shift_id}/workers",
)
def list_shift_workers(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    try:
        assignments = (
            shift_service.list_shift_workers(
                db,
                shift_id,
            )
        )

        return [
            {
                "id": assignment.id,
                "shift_id": assignment.shift_id,
                "worker_id": assignment.worker_id,
                "assigned_at": assignment.assigned_at,
            }
            for assignment in assignments
        ]

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.delete(
    "/{shift_id}/workers/{worker_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_worker(
    shift_id: int,
    worker_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*SUPERVISION_ROLES)
    ),
):
    try:
        shift_service.remove_worker(
            db,
            shift_id,
            worker_id,
        )
    except ValueError as exc:
        message = str(exc)

        if message in {
            "Worker is not assigned to this shift",
            "Shift not found",
        }:
            raise HTTPException(
                status_code=404,
                detail=message,
            )

        raise HTTPException(
            status_code=400,
            detail=message,
        )