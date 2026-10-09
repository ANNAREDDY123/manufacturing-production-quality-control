from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.raw_material import RawMaterialStatus


class RawMaterialCreate(BaseModel):
    material_code: str = Field(
        min_length=2,
        max_length=50,
    )

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    category: str = Field(
        min_length=2,
        max_length=100,
    )

    unit: str = Field(
        min_length=1,
        max_length=30,
    )

    supplier: str = Field(
        min_length=2,
        max_length=150,
    )

    available_quantity: float = Field(
        default=0,
        ge=0,
    )

    minimum_stock: float = Field(
        default=0,
        ge=0,
    )

    reorder_level: float = Field(
        default=0,
        ge=0,
    )

    status: RawMaterialStatus = RawMaterialStatus.ACTIVE


class RawMaterialUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    category: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    unit: str | None = Field(
        default=None,
        min_length=1,
        max_length=30,
    )

    supplier: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    minimum_stock: float | None = Field(
        default=None,
        ge=0,
    )

    reorder_level: float | None = Field(
        default=None,
        ge=0,
    )


class RawMaterialStatusUpdate(BaseModel):
    status: RawMaterialStatus


class RawMaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    material_code: str
    name: str
    category: str
    unit: str
    supplier: str
    available_quantity: float
    minimum_stock: float
    reorder_level: float
    status: RawMaterialStatus
    created_at: datetime
    updated_at: datetime


class StockMovementCreate(BaseModel):
    quantity: float = Field(
        gt=0,
    )

    reference: str | None = Field(
        default=None,
        max_length=255,
    )

    remarks: str | None = Field(
        default=None,
        max_length=500,
    )


class StockAdjustmentCreate(BaseModel):
    quantity: float = Field(
        ge=0,
    )

    reference: str | None = Field(
        default=None,
        max_length=255,
    )

    remarks: str | None = Field(
        default=None,
        max_length=500,
    )


class InventoryMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    material_id: int
    movement_type: str
    quantity: float
    previous_quantity: float
    new_quantity: float
    reference: str | None
    remarks: str | None
    created_by: int | None
    created_at: datetime