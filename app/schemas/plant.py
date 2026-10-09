from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.plant import PlantStatus


class PlantCreate(BaseModel):
    plant_code: str = Field(
        min_length=2,
        max_length=50,
    )

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    description: str | None = None

    address: str = Field(
        min_length=3,
        max_length=255,
    )

    city: str = Field(
        min_length=2,
        max_length=100,
    )

    state: str = Field(
        min_length=2,
        max_length=100,
    )

    country: str = Field(
        min_length=2,
        max_length=100,
        default="India",
    )

    capacity: float = Field(
        gt=0,
    )

    manager_id: int | None = None

    status: PlantStatus = PlantStatus.ACTIVE


class PlantUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    description: str | None = None

    address: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
    )

    city: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    state: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    country: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    capacity: float | None = Field(
        default=None,
        gt=0,
    )

    manager_id: int | None = None


class PlantStatusUpdate(BaseModel):
    status: PlantStatus


class PlantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plant_code: str
    name: str
    description: str | None
    address: str
    city: str
    state: str
    country: str
    capacity: float
    status: PlantStatus
    manager_id: int | None
    created_at: datetime
    updated_at: datetime