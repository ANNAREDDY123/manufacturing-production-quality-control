from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.bom import BOM, BOMItem, BOMStatus
from app.models.product import Product
from app.models.raw_material import RawMaterial
from app.schemas.bom import (
    BOMCreate,
    BOMItemCreate,
    BOMItemUpdate,
    BOMUpdate,
)


def _get_product(
    db: Session,
    product_id: int,
) -> Product:
    product = db.scalar(
        select(Product).where(
            Product.id == product_id
        )
    )

    if product is None:
        raise ValueError("Product not found")

    return product


def _get_bom(
    db: Session,
    bom_id: int,
) -> BOM:
    bom = db.scalar(
        select(BOM).where(
            BOM.id == bom_id
        )
    )

    if bom is None:
        raise ValueError("BOM not found")

    return bom


def _get_material(
    db: Session,
    material_id: int,
) -> RawMaterial:
    material = db.scalar(
        select(RawMaterial).where(
            RawMaterial.id == material_id
        )
    )

    if material is None:
        raise ValueError("Raw material not found")

    if material.status.value != "Active":
        raise ValueError(
            "Cannot use an inactive raw material in BOM"
        )

    return material


def _validate_items(
    db: Session,
    items: list[BOMItemCreate],
) -> list[RawMaterial]:
    material_ids = [
        item.material_id
        for item in items
    ]

    if len(material_ids) != len(set(material_ids)):
        raise ValueError(
            "A raw material cannot appear more than once in the same BOM"
        )

    return [
        _get_material(db, material_id)
        for material_id in material_ids
    ]


def create_bom(
    db: Session,
    product_id: int,
    data: BOMCreate,
) -> BOM:
    _get_product(db, product_id)

    materials = _validate_items(
        db,
        data.items,
    )

    if data.version is None:
        max_version = db.scalar(
            select(func.max(BOM.version)).where(
                BOM.product_id == product_id
            )
        )

        version = (max_version or 0) + 1

    else:
        version = data.version

        existing = db.scalar(
            select(BOM).where(
                BOM.product_id == product_id,
                BOM.version == version,
            )
        )

        if existing:
            raise ValueError(
                f"BOM version {version} already exists for this product"
            )

    bom = BOM(
        product_id=product_id,
        version=version,
        status=BOMStatus.INACTIVE,
        description=data.description,
    )

    db.add(bom)
    db.flush()

    for item_data, material in zip(
        data.items,
        materials,
    ):
        bom.items.append(
            BOMItem(
                material_id=material.id,
                quantity=item_data.quantity,
                unit=material.unit,
            )
        )

    db.commit()
    db.refresh(bom)

    return bom


def get_bom(
    db: Session,
    bom_id: int,
) -> BOM:
    return _get_bom(
        db,
        bom_id,
    )


def list_boms(
    db: Session,
    product_id: int,
    status: BOMStatus | None = None,
) -> list[BOM]:
    _get_product(
        db,
        product_id,
    )

    query = select(BOM).where(
        BOM.product_id == product_id
    )

    if status is not None:
        query = query.where(
            BOM.status == status
        )

    query = query.order_by(
        BOM.version.desc()
    )

    return list(
        db.scalars(query).all()
    )


def update_bom(
    db: Session,
    bom_id: int,
    data: BOMUpdate,
) -> BOM:
    bom = _get_bom(
        db,
        bom_id,
    )

    if bom.status == BOMStatus.ACTIVE:
        raise ValueError(
            "Cannot modify an active BOM. Deactivate it first."
        )

    if data.description is not None:
        bom.description = data.description

    db.commit()
    db.refresh(bom)

    return bom


def add_bom_item(
    db: Session,
    bom_id: int,
    data: BOMItemCreate,
) -> BOMItem:
    bom = _get_bom(
        db,
        bom_id,
    )

    if bom.status == BOMStatus.ACTIVE:
        raise ValueError(
            "Cannot modify an active BOM. Deactivate it first."
        )

    material = _get_material(
        db,
        data.material_id,
    )

    existing = db.scalar(
        select(BOMItem).where(
            BOMItem.bom_id == bom_id,
            BOMItem.material_id == data.material_id,
        )
    )

    if existing:
        raise ValueError(
            "Raw material already exists in this BOM"
        )

    item = BOMItem(
        bom_id=bom.id,
        material_id=material.id,
        quantity=data.quantity,
        unit=material.unit,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


def update_bom_item(
    db: Session,
    bom_id: int,
    item_id: int,
    data: BOMItemUpdate,
) -> BOMItem:
    bom = _get_bom(
        db,
        bom_id,
    )

    if bom.status == BOMStatus.ACTIVE:
        raise ValueError(
            "Cannot modify an active BOM. Deactivate it first."
        )

    item = db.scalar(
        select(BOMItem).where(
            BOMItem.id == item_id,
            BOMItem.bom_id == bom_id,
        )
    )

    if item is None:
        raise ValueError(
            "BOM item not found"
        )

    item.quantity = data.quantity

    db.commit()
    db.refresh(item)

    return item


def remove_bom_item(
    db: Session,
    bom_id: int,
    item_id: int,
) -> None:
    bom = _get_bom(
        db,
        bom_id,
    )

    if bom.status == BOMStatus.ACTIVE:
        raise ValueError(
            "Cannot modify an active BOM. Deactivate it first."
        )

    item = db.scalar(
        select(BOMItem).where(
            BOMItem.id == item_id,
            BOMItem.bom_id == bom_id,
        )
    )

    if item is None:
        raise ValueError(
            "BOM item not found"
        )

    remaining_items = db.scalar(
        select(func.count(BOMItem.id)).where(
            BOMItem.bom_id == bom_id,
            BOMItem.id != item_id,
        )
    )

    if remaining_items == 0:
        raise ValueError(
            "A BOM must contain at least one raw material"
        )

    db.delete(item)
    db.commit()


def update_bom_status(
    db: Session,
    bom_id: int,
    status: BOMStatus,
) -> BOM:
    bom = _get_bom(
        db,
        bom_id,
    )

    if status == BOMStatus.ACTIVE:
        if not bom.items:
            raise ValueError(
                "Cannot activate a BOM without raw materials"
            )

        active_bom = db.scalar(
            select(BOM).where(
                BOM.product_id == bom.product_id,
                BOM.status == BOMStatus.ACTIVE,
                BOM.id != bom.id,
            )
        )

        if active_bom:
            active_bom.status = BOMStatus.INACTIVE

    bom.status = status

    db.commit()
    db.refresh(bom)

    return bom