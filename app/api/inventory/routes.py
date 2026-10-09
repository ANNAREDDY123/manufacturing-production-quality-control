from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import require_roles
from app.db.database import get_db
from app.models.inventory_movement import InventoryMovementType
from app.models.user import UserRole
from app.schemas.inventory_movement import (
    InventoryMovementCreate,
    InventoryMovementResponse,
    InventoryMovementUpdate,
)
from app.services.inventory_movement_service import (
    create_inventory_movement,
    delete_inventory_movement,
    get_inventory_movement,
    list_inventory_movements,
    update_inventory_movement,
)


router = APIRouter(
    prefix="/inventory-movements",
    tags=["Inventory Movements"],
)


MANAGE_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.STORE_MANAGER,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
)


VIEW_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.STORE_MANAGER,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
    UserRole.QUALITY_MANAGER,
)


@router.post(
    "",
    response_model=InventoryMovementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: InventoryMovementCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    return create_inventory_movement(
        db,
        data,
        current_user.id,
    )


@router.get(
    "",
    response_model=list[InventoryMovementResponse],
)
def list_all(
    material_id: int | None = Query(
        default=None,
        gt=0,
    ),
    movement_type: InventoryMovementType | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    return list_inventory_movements(
        db,
        material_id=material_id,
        movement_type=movement_type,
    )


@router.get(
    "/{movement_id}",
    response_model=InventoryMovementResponse,
)
def get_one(
    movement_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    return get_inventory_movement(
        db,
        movement_id,
    )


@router.put(
    "/{movement_id}",
    response_model=InventoryMovementResponse,
)
def update(
    movement_id: int,
    data: InventoryMovementUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    return update_inventory_movement(
        db,
        movement_id,
        data,
    )


@router.delete(
    "/{movement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    movement_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    delete_inventory_movement(
        db,
        movement_id,
    )