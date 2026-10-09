from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.inventory_movement import (
    InventoryMovement,
    InventoryMovementType,
)
from app.models.raw_material import (
    RawMaterial,
    RawMaterialStatus,
)
from app.schemas.raw_material import (
    RawMaterialCreate,
    RawMaterialUpdate,
    StockAdjustmentCreate,
    StockMovementCreate,
)


def create_raw_material(
    db: Session,
    material_data: RawMaterialCreate,
) -> RawMaterial:

    existing = db.scalar(
        select(RawMaterial).where(
            RawMaterial.material_code
            == material_data.material_code
        )
    )

    if existing:
        raise ValueError(
            "Material code already exists"
        )

    material = RawMaterial(
        material_code=material_data.material_code,
        name=material_data.name,
        category=material_data.category,
        unit=material_data.unit,
        supplier=material_data.supplier,
        available_quantity=material_data.available_quantity,
        minimum_stock=material_data.minimum_stock,
        reorder_level=material_data.reorder_level,
        status=material_data.status,
    )

    db.add(material)
    db.commit()
    db.refresh(material)

    # Record initial quantity as stock-in history.
    if material_data.available_quantity > 0:
        movement = InventoryMovement(
            material_id=material.id,
            movement_type=InventoryMovementType.STOCK_IN,
            quantity=material_data.available_quantity,
            previous_quantity=0,
            new_quantity=material_data.available_quantity,
            reference="Initial Stock",
        )

        db.add(movement)
        db.commit()

    return material


def get_raw_material(
    db: Session,
    material_id: int,
) -> RawMaterial | None:

    return db.scalar(
        select(RawMaterial).where(
            RawMaterial.id == material_id
        )
    )


def list_raw_materials(
    db: Session,
    search: str | None = None,
    category: str | None = None,
    status: RawMaterialStatus | None = None,
    low_stock: bool = False,
    skip: int = 0,
    limit: int = 20,
) -> list[RawMaterial]:

    query = select(RawMaterial)

    if search:
        search_value = f"%{search}%"

        query = query.where(
            or_(
                RawMaterial.material_code.ilike(
                    search_value
                ),
                RawMaterial.name.ilike(
                    search_value
                ),
                RawMaterial.supplier.ilike(
                    search_value
                ),
            )
        )

    if category:
        query = query.where(
            RawMaterial.category.ilike(category)
        )

    if status:
        query = query.where(
            RawMaterial.status == status
        )

    if low_stock:
        query = query.where(
            RawMaterial.available_quantity
            <= RawMaterial.reorder_level
        )

    query = (
        query
        .order_by(RawMaterial.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(
        db.scalars(query).all()
    )


def update_raw_material(
    db: Session,
    material: RawMaterial,
    material_data: RawMaterialUpdate,
) -> RawMaterial:

    update_data = material_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            material,
            field,
            value,
        )

    db.commit()
    db.refresh(material)

    return material


def update_raw_material_status(
    db: Session,
    material: RawMaterial,
    status: RawMaterialStatus,
) -> RawMaterial:

    material.status = status

    db.commit()
    db.refresh(material)

    return material


def delete_raw_material(
    db: Session,
    material: RawMaterial,
) -> None:

    existing_movements = db.scalar(
        select(InventoryMovement).where(
            InventoryMovement.material_id
            == material.id
        )
    )

    if existing_movements:
        raise ValueError(
            "Cannot delete material with inventory history"
        )

    db.delete(material)
    db.commit()


def record_stock_in(
    db: Session,
    material: RawMaterial,
    movement_data: StockMovementCreate,
    user_id: int,
) -> InventoryMovement:

    if material.status == RawMaterialStatus.INACTIVE:
        raise ValueError(
            "Cannot add stock to an inactive material"
        )

    previous_quantity = material.available_quantity

    material.available_quantity += movement_data.quantity

    movement = InventoryMovement(
        material_id=material.id,
        movement_type=InventoryMovementType.STOCK_IN,
        quantity=movement_data.quantity,
        previous_quantity=previous_quantity,
        new_quantity=material.available_quantity,
        reference=movement_data.reference,
        remarks=movement_data.remarks,
        created_by=user_id,
    )

    db.add(movement)
    db.commit()
    db.refresh(movement)

    return movement


def record_stock_out(
    db: Session,
    material: RawMaterial,
    movement_data: StockMovementCreate,
    user_id: int,
) -> InventoryMovement:

    if material.status == RawMaterialStatus.INACTIVE:
        raise ValueError(
            "Cannot consume stock from an inactive material"
        )

    if (
        movement_data.quantity
        > material.available_quantity
    ):
        raise ValueError(
            "Insufficient inventory: stock cannot become negative"
        )

    previous_quantity = material.available_quantity

    material.available_quantity -= movement_data.quantity

    movement = InventoryMovement(
        material_id=material.id,
        movement_type=InventoryMovementType.STOCK_OUT,
        quantity=movement_data.quantity,
        previous_quantity=previous_quantity,
        new_quantity=material.available_quantity,
        reference=movement_data.reference,
        remarks=movement_data.remarks,
        created_by=user_id,
    )

    db.add(movement)
    db.commit()
    db.refresh(movement)

    return movement


def adjust_stock(
    db: Session,
    material: RawMaterial,
    adjustment_data: StockAdjustmentCreate,
    user_id: int,
) -> InventoryMovement:

    previous_quantity = material.available_quantity

    material.available_quantity = (
        adjustment_data.quantity
    )

    movement = InventoryMovement(
        material_id=material.id,
        movement_type=InventoryMovementType.ADJUSTMENT,
        quantity=adjustment_data.quantity,
        previous_quantity=previous_quantity,
        new_quantity=material.available_quantity,
        reference=adjustment_data.reference,
        remarks=adjustment_data.remarks,
        created_by=user_id,
    )

    db.add(movement)
    db.commit()
    db.refresh(movement)

    return movement


def get_inventory_history(
    db: Session,
    material_id: int,
    skip: int = 0,
    limit: int = 50,
) -> list[InventoryMovement]:

    query = (
        select(InventoryMovement)
        .where(
            InventoryMovement.material_id
            == material_id
        )
        .order_by(
            InventoryMovement.id.desc()
        )
        .offset(skip)
        .limit(limit)
    )

    return list(
        db.scalars(query).all()
    )