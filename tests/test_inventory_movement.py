from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.inventory_movement import (
    InventoryMovementType,
)
from app.schemas.inventory_movement import (
    InventoryMovementCreate,
    InventoryMovementUpdate,
)


def test_inventory_movement_create_schema():
    data = InventoryMovementCreate(
        material_id=1,
        movement_type=InventoryMovementType.STOCK_IN,
        quantity=100,
        reference="PO-001",
        remarks="Material received",
    )

    assert data.material_id == 1
    assert data.movement_type == InventoryMovementType.STOCK_IN
    assert data.quantity == 100


def test_stock_out_schema():
    data = InventoryMovementCreate(
        material_id=1,
        movement_type=InventoryMovementType.STOCK_OUT,
        quantity=25,
    )

    assert data.movement_type == InventoryMovementType.STOCK_OUT
    assert data.quantity == 25


def test_adjustment_schema():
    data = InventoryMovementCreate(
        material_id=1,
        movement_type=InventoryMovementType.ADJUSTMENT,
        quantity=75,
    )

    assert data.movement_type == InventoryMovementType.ADJUSTMENT
    assert data.quantity == 75


def test_stock_adjustment_alias():
    assert (
        InventoryMovementType.STOCK_ADJUSTMENT
        == InventoryMovementType.ADJUSTMENT
    )


def test_invalid_material_id():
    with pytest.raises(ValidationError):
        InventoryMovementCreate(
            material_id=0,
            movement_type=InventoryMovementType.STOCK_IN,
            quantity=10,
        )


def test_invalid_quantity():
    with pytest.raises(ValidationError):
        InventoryMovementCreate(
            material_id=1,
            movement_type=InventoryMovementType.STOCK_IN,
            quantity=0,
        )


def test_negative_quantity():
    with pytest.raises(ValidationError):
        InventoryMovementCreate(
            material_id=1,
            movement_type=InventoryMovementType.STOCK_OUT,
            quantity=-5,
        )


def test_update_schema():
    data = InventoryMovementUpdate(
        reference="UPDATED-REF",
        remarks="Updated remarks",
    )

    assert data.reference == "UPDATED-REF"
    assert data.remarks == "Updated remarks"


def test_enum_values():
    assert InventoryMovementType.STOCK_IN.value == "Stock In"
    assert InventoryMovementType.STOCK_OUT.value == "Stock Out"
    assert InventoryMovementType.ADJUSTMENT.value == "Adjustment"