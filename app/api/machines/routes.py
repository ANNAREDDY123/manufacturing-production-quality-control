from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import require_roles
from app.db.database import get_db
from app.models.machine import MachineStatus
from app.models.user import User, UserRole
from app.schemas.machine import (
    MachineCreate,
    MachineResponse,
    MachineStatusUpdate,
    MachineUpdate,
)
from app.services.machine_service import (
    create_machine,
    delete_machine,
    get_machine,
    list_machines,
    update_machine,
    update_machine_status,
)


router = APIRouter(
    prefix="/machines",
    tags=["Machines"],
)


MANAGEMENT_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.MAINTENANCE_ENGINEER,
)

VIEW_ROLES = tuple(
    role
    for role in UserRole
    if role != UserRole.WORKER
)


@router.post(
    "",
    response_model=MachineResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_machine_endpoint(
    data: MachineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        return create_machine(
            db,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[MachineResponse],
)
def get_machines(
    search: str | None = Query(
        default=None,
        min_length=1,
    ),
    machine_type: str | None = Query(
        default=None,
        min_length=1,
    ),
    production_line_id: int | None = Query(
        default=None,
        gt=0,
    ),
    status_filter: MachineStatus | None = None,
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    return list_machines(
        db,
        search=search,
        machine_type=machine_type,
        production_line_id=production_line_id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{machine_id}",
    response_model=MachineResponse,
)
def get_machine_details(
    machine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    try:
        return get_machine(
            db,
            machine_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.put(
    "/{machine_id}",
    response_model=MachineResponse,
)
def update_machine_endpoint(
    machine_id: int,
    data: MachineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        return update_machine(
            db,
            machine_id,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{machine_id}/status",
    response_model=MachineResponse,
)
def update_machine_status_endpoint(
    machine_id: int,
    data: MachineStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        return update_machine_status(
            db,
            machine_id,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{machine_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_machine_endpoint(
    machine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        delete_machine(
            db,
            machine_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc