from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.inventory_movement import InventoryMovementType


class InventoryMovementCreate(BaseModel):
    material_id: int = Field(gt=0)

    movement_type: InventoryMovementType

    quantity: float = Field(gt=0)

    reference: str | None = Field(
        default=None,
        max_length=255,
    )

    remarks: str | None = Field(
        default=None,
        max_length=500,
    )


class InventoryMovementUpdate(BaseModel):
    reference: str | None = Field(
        default=None,
        max_length=255,
    )

    remarks: str | None = Field(
        default=None,
        max_length=500,
    )


class InventoryMovementResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    material_id: int
    movement_type: InventoryMovementType
    quantity: float
    previous_quantity: float
    new_quantity: float
    reference: str | None
    remarks: str | None
    created_by: int | None
    created_at: datetime