from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.product import ProductStatus


class ProductCreate(BaseModel):
    product_code: str = Field(
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

    sku: str = Field(
        min_length=2,
        max_length=100,
    )

    unit: str = Field(
        min_length=1,
        max_length=30,
    )

    standard_production_time: float = Field(
        gt=0,
    )

    status: ProductStatus = ProductStatus.ACTIVE


class ProductUpdate(BaseModel):
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

    sku: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    unit: str | None = Field(
        default=None,
        min_length=1,
        max_length=30,
    )

    standard_production_time: float | None = Field(
        default=None,
        gt=0,
    )


class ProductStatusUpdate(BaseModel):
    status: ProductStatus


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_code: str
    name: str
    category: str
    sku: str
    unit: str
    standard_production_time: float
    status: ProductStatus
    created_at: datetime
    updated_at: datetime