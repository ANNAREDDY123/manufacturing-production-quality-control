from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import require_roles
from app.db.database import get_db
from app.models.raw_material import RawMaterialStatus
from app.models.user import User, UserRole
from app.schemas.raw_material import (
    InventoryMovementResponse,
    RawMaterialCreate,
    RawMaterialResponse,
    RawMaterialStatusUpdate,
    RawMaterialUpdate,
    StockAdjustmentCreate,
    StockMovementCreate,
)
from app.services.raw_material_service import (
    adjust_stock,
    create_raw_material,
    delete_raw_material,
    get_inventory_history,
    get_raw_material,
    list_raw_materials,
    record_stock_in,
    record_stock_out,
    update_raw_material,
    update_raw_material_status,
)


router = APIRouter(
    prefix="/raw-materials",
    tags=["Raw Materials"],
)


management_roles = require_roles(
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.STORE_MANAGER,
)


inventory_roles = require_roles(
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.STORE_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
)


view_roles = require_roles(
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.QUALITY_MANAGER,
    UserRole.MAINTENANCE_ENGINEER,
    UserRole.STORE_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
)


@router.post(
    "",
    response_model=RawMaterialResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_material(
    material_data: RawMaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(management_roles),
):
    try:
        return create_raw_material(
            db,
            material_data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[RawMaterialResponse],
)
def get_materials(
    search: str | None = Query(
        default=None,
        min_length=1,
    ),
    category: str | None = Query(
        default=None,
        min_length=1,
    ),
    status_filter: RawMaterialStatus | None = Query(
        default=None,
        alias="status",
    ),
    low_stock: bool = Query(
        default=False,
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
    current_user: User = Depends(view_roles),
):
    return list_raw_materials(
        db,
        search=search,
        category=category,
        status=status_filter,
        low_stock=low_stock,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{material_id}",
    response_model=RawMaterialResponse,
)
def get_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(view_roles),
):
    material = get_raw_material(
        db,
        material_id,
    )

    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw material not found",
        )

    return material


@router.put(
    "/{material_id}",
    response_model=RawMaterialResponse,
)
def update_material(
    material_id: int,
    material_data: RawMaterialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(management_roles),
):
    material = get_raw_material(
        db,
        material_id,
    )

    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw material not found",
        )

    return update_raw_material(
        db,
        material,
        material_data,
    )


@router.patch(
    "/{material_id}/status",
    response_model=RawMaterialResponse,
)
def update_material_status(
    material_id: int,
    status_data: RawMaterialStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(management_roles),
):
    material = get_raw_material(
        db,
        material_id,
    )

    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw material not found",
        )

    return update_raw_material_status(
        db,
        material,
        status_data.status,
    )


@router.delete(
    "/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(management_roles),
):
    material = get_raw_material(
        db,
        material_id,
    )

    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw material not found",
        )

    try:
        delete_raw_material(
            db,
            material,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return None


@router.post(
    "/{material_id}/stock-in",
    response_model=InventoryMovementResponse,
)
def stock_in(
    material_id: int,
    movement_data: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(inventory_roles),
):
    material = get_raw_material(
        db,
        material_id,
    )

    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw material not found",
        )

    try:
        return record_stock_in(
            db,
            material,
            movement_data,
            current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{material_id}/stock-out",
    response_model=InventoryMovementResponse,
)
def stock_out(
    material_id: int,
    movement_data: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(inventory_roles),
):
    material = get_raw_material(
        db,
        material_id,
    )

    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw material not found",
        )

    try:
        return record_stock_out(
            db,
            material,
            movement_data,
            current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{material_id}/adjust-stock",
    response_model=InventoryMovementResponse,
)
def adjust_material_stock(
    material_id: int,
    adjustment_data: StockAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(inventory_roles),
):
    material = get_raw_material(
        db,
        material_id,
    )

    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw material not found",
        )

    return adjust_stock(
        db,
        material,
        adjustment_data,
        current_user.id,
    )


@router.get(
    "/{material_id}/history",
    response_model=list[InventoryMovementResponse],
)
def inventory_history(
    material_id: int,
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(view_roles),
):
    material = get_raw_material(
        db,
        material_id,
    )

    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw material not found",
        )

    return get_inventory_history(
        db,
        material_id,
        skip=skip,
        limit=limit,
    )