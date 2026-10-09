from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import require_roles
from app.db.database import get_db
from app.models.production_order import (
    ProductionOrderPriority,
    ProductionOrderStatus,
)
from app.models.user import User, UserRole
from app.schemas.production_order import (
    ProductionOrderCreate,
    ProductionOrderResponse,
    ProductionOrderStatusUpdate,
    ProductionOrderUpdate,
)
from app.services.production_order_service import (
    create_production_order,
    get_production_order,
    list_production_orders,
    update_production_order,
    update_production_order_status,
)


router = APIRouter(
    prefix="/production-orders",
    tags=["Production Orders"],
)


MANAGEMENT_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
)

STATUS_MANAGEMENT_ROLES = (
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


@router.post(
    "",
    response_model=ProductionOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    data: ProductionOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        return create_production_order(
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
    response_model=list[ProductionOrderResponse],
)
def get_orders(
    search: str | None = Query(
        default=None,
        min_length=1,
    ),
    product_id: int | None = Query(
        default=None,
        gt=0,
    ),
    production_line_id: int | None = Query(
        default=None,
        gt=0,
    ),
    status_filter: ProductionOrderStatus | None = None,
    priority: ProductionOrderPriority | None = None,
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
    return list_production_orders(
        db,
        search=search,
        product_id=product_id,
        production_line_id=production_line_id,
        status=status_filter,
        priority=priority,
        supervisor_id=supervisor_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{order_id}",
    response_model=ProductionOrderResponse,
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    try:
        return get_production_order(
            db,
            order_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.put(
    "/{order_id}",
    response_model=ProductionOrderResponse,
)
def update_order(
    order_id: int,
    data: ProductionOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        return update_production_order(
            db,
            order_id,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{order_id}/status",
    response_model=ProductionOrderResponse,
)
def change_order_status(
    order_id: int,
    data: ProductionOrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*STATUS_MANAGEMENT_ROLES)
    ),
):
    try:
        return update_production_order_status(
            db,
            order_id,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc