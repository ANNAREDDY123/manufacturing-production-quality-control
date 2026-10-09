from pydantic import BaseModel, ConfigDict, Field

from app.models.bom import BOMStatus


class BOMItemCreate(BaseModel):
    material_id: int = Field(gt=0)
    quantity: float = Field(gt=0)


class BOMItemUpdate(BaseModel):
    quantity: float = Field(gt=0)


class BOMCreate(BaseModel):
    version: int | None = Field(
        default=None,
        gt=0,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    items: list[BOMItemCreate] = Field(
        min_length=1,
    )


class BOMUpdate(BaseModel):
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class BOMStatusUpdate(BaseModel):
    status: BOMStatus


class BOMItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    material_id: int
    quantity: float
    unit: str


class BOMResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    product_id: int
    version: int
    status: BOMStatus
    description: str | None
    items: list[BOMItemResponse]