from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.production_order import (
    ProductionOrderPriority,
    ProductionOrderStatus,
)


class ProductionOrderCreate(BaseModel):
    order_number: str = Field(
        min_length=2,
        max_length=50,
    )

    product_id: int = Field(
        gt=0,
    )

    quantity: float = Field(
        gt=0,
    )

    target_date: date

    production_line_id: int = Field(
        gt=0,
    )

    priority: ProductionOrderPriority = (
        ProductionOrderPriority.MEDIUM
    )

    supervisor_id: int | None = Field(
        default=None,
        gt=0,
    )


class ProductionOrderUpdate(BaseModel):
    quantity: float | None = Field(
        default=None,
        gt=0,
    )

    target_date: date | None = None

    production_line_id: int | None = Field(
        default=None,
        gt=0,
    )

    priority: ProductionOrderPriority | None = None

    supervisor_id: int | None = Field(
        default=None,
        gt=0,
    )


class ProductionOrderStatusUpdate(BaseModel):
    status: ProductionOrderStatus


class ProductionOrderResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    order_number: str
    product_id: int
    quantity: float
    target_date: date
    production_line_id: int
    priority: ProductionOrderPriority
    supervisor_id: int | None
    status: ProductionOrderStatus
    created_by: int | None
    created_at: object
    updated_at: object