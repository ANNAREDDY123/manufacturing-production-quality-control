from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.production_line import ProductionLineStatus


class ProductionLineCreate(BaseModel):
    line_code: str = Field(
        min_length=2,
        max_length=50,
    )

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    capacity: float = Field(
        gt=0,
    )

    plant_id: int = Field(
        gt=0,
    )

    supervisor_id: int | None = Field(
        default=None,
        gt=0,
    )

    status: ProductionLineStatus = ProductionLineStatus.ACTIVE


class ProductionLineUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    capacity: float | None = Field(
        default=None,
        gt=0,
    )

    plant_id: int | None = Field(
        default=None,
        gt=0,
    )

    supervisor_id: int | None = Field(
        default=None,
        gt=0,
    )


class ProductionLineStatusUpdate(BaseModel):
    status: ProductionLineStatus


class ProductionLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    line_code: str
    name: str
    capacity: float
    plant_id: int
    supervisor_id: int | None
    status: ProductionLineStatus
    created_at: datetime
    updated_at: datetime