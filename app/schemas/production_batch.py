from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.production_batch import ProductionBatchStatus


class ProductionBatchCreate(BaseModel):
    batch_number: str = Field(
        min_length=2,
        max_length=50,
    )

    production_order_id: int = Field(
        gt=0,
    )

    quantity: float = Field(
        gt=0,
    )

    supervisor_id: int | None = Field(
        default=None,
        gt=0,
    )

    planned_start: datetime | None = None


class ProductionBatchUpdate(BaseModel):
    quantity: float | None = Field(
        default=None,
        gt=0,
    )

    supervisor_id: int | None = Field(
        default=None,
        gt=0,
    )

    planned_start: datetime | None = None


class ProductionBatchStatusUpdate(BaseModel):
    status: ProductionBatchStatus


class ProductionBatchResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    batch_number: str
    production_order_id: int
    quantity: float
    supervisor_id: int | None
    status: ProductionBatchStatus
    planned_start: datetime | None
    actual_start: datetime | None
    actual_end: datetime | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime