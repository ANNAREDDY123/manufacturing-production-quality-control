from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import HTTPException, status

from app.models.inventory_movement import InventoryMovement
from app.models.raw_material import RawMaterial
from app.models.user import User
from app.schemas.inventory_movement import (
    InventoryMovementCreate,
    InventoryMovementUpdate,
)


def _get_movement(
    db: Session,
    movement_id: int,
) -> InventoryMovement:
    movement = db.scalar(
        select(InventoryMovement).where(
            InventoryMovement.id == movement_id
        )
    )

    if movement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory movement not found",
        )

    return movement


def _validate_material(
    db: Session,
    material_id: int,
) -> RawMaterial:
    material = db.scalar(
        select(RawMaterial).where(
            RawMaterial.id == material_id
        )
    )

    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw material not found",
        )

    return material


def _validate_user(
    db: Session,
    user_id: int,
) -> User:
    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


def create_inventory_movement(
    db: Session,
    data: InventoryMovementCreate,
    user_id: int,
) -> InventoryMovement:

    material = _validate_material(
        db,
        data.material_id,
    )

    _validate_user(
        db,
        user_id,
    )

    previous_quantity = material.available_quantity

    if data.movement_type == InventoryMovementType.STOCK_IN:
        new_quantity = (
            previous_quantity + data.quantity
        )

    elif data.movement_type == InventoryMovementType.STOCK_OUT:
        if data.quantity > previous_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Insufficient inventory: "
                    "stock cannot become negative"
                ),
            )

        new_quantity = (
            previous_quantity - data.quantity
        )

    elif data.movement_type in (
        InventoryMovementType.ADJUSTMENT,
        InventoryMovementType.STOCK_ADJUSTMENT,
    ):
        new_quantity = data.quantity

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported inventory movement type",
        )

    material.available_quantity = new_quantity

    movement = InventoryMovement(
        material_id=data.material_id,
        movement_type=data.movement_type,
        quantity=data.quantity,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        reference=data.reference,
        remarks=data.remarks,
        created_by=user_id,
    )

    db.add(movement)
    db.commit()
    db.refresh(movement)

    return movement


def list_inventory_movements(
    db: Session,
    material_id: int | None = None,
    movement_type: InventoryMovementType | None = None,
):
    query = select(
        InventoryMovement
    ).order_by(
        InventoryMovement.id.desc()
    )

    if material_id is not None:
        query = query.where(
            InventoryMovement.material_id
            == material_id
        )

    if movement_type is not None:
        query = query.where(
            InventoryMovement.movement_type
            == movement_type
        )

    return list(
        db.scalars(query).all()
    )


def get_inventory_movement(
    db: Session,
    movement_id: int,
) -> InventoryMovement:
    return _get_movement(
        db,
        movement_id,
    )


def update_inventory_movement(
    db: Session,
    movement_id: int,
    data: InventoryMovementUpdate,
) -> InventoryMovement:

    movement = _get_movement(
        db,
        movement_id,
    )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            movement,
            field,
            value,
        )

    db.commit()
    db.refresh(movement)

    return movement


def delete_inventory_movement(
    db: Session,
    movement_id: int,
) -> None:

    movement = _get_movement(
        db,
        movement_id,
    )

    db.delete(movement)
    db.commit()