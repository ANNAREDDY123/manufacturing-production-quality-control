from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import require_roles
from app.db.database import get_db
from app.models.production_batch import ProductionBatchStatus
from app.models.user import User, UserRole
from app.schemas.production_batch import (
    ProductionBatchCreate,
    ProductionBatchResponse,
    ProductionBatchStatusUpdate,
    ProductionBatchUpdate,
)
from app.services.production_batch_service import (
    create_production_batch,
    get_production_batch,
    list_production_batches,
    update_production_batch,
    update_production_batch_status,
)


MANAGEMENT_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
)

STATUS_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
)

VIEW_ROLES = tuple(
    role
    for role in UserRole
    if role != UserRole.WORKER
)


router = APIRouter(
    prefix="/production-batches",
    tags=["Production Batches"],
)


@router.post(
    "",
    response_model=ProductionBatchResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_batch(
    data: ProductionBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        return create_production_batch(
            db,
            data,
            created_by=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[ProductionBatchResponse],
)
def get_batches(
    search: str | None = Query(
        default=None,
        min_length=1,
    ),
    production_order_id: int | None = Query(
        default=None,
        gt=0,
    ),
    status_filter: ProductionBatchStatus | None = Query(
        default=None,
        alias="status",
    ),
    supervisor_id: int | None = Query(
        default=None,
        gt=0,
    ),
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
    return list_production_batches(
        db,
        search=search,
        production_order_id=production_order_id,
        status=status_filter,
        supervisor_id=supervisor_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{batch_id}",
    response_model=ProductionBatchResponse,
)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    try:
        return get_production_batch(
            db,
            batch_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.put(
    "/{batch_id}",
    response_model=ProductionBatchResponse,
)
def update_batch(
    batch_id: int,
    data: ProductionBatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        return update_production_batch(
            db,
            batch_id,
            data,
        )
    except ValueError as exc:
        if str(exc) == "Production batch not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{batch_id}/status",
    response_model=ProductionBatchResponse,
)
def change_batch_status(
    batch_id: int,
    data: ProductionBatchStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*STATUS_ROLES)
    ),
):
    try:
        return update_production_batch_status(
            db,
            batch_id,
            data,
        )
    except ValueError as exc:
        if str(exc) == "Production batch not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc