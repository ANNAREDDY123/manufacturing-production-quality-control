from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.worker import WorkerStatus


class WorkerCreate(BaseModel):
    employee_code: str = Field(
        min_length=2,
        max_length=50,
    )

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    skill: str = Field(
        min_length=2,
        max_length=100,
    )

    department: str = Field(
        min_length=2,
        max_length=100,
    )

    shift: str = Field(
        min_length=2,
        max_length=50,
    )

    production_line_id: int | None = Field(
        default=None,
        gt=0,
    )

    status: WorkerStatus = WorkerStatus.ACTIVE


class WorkerUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    skill: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    department: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    shift: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
    )

    production_line_id: int | None = Field(
        default=None,
        gt=0,
    )

    status: WorkerStatus | None = None


class WorkerStatusUpdate(BaseModel):
    status: WorkerStatus


class WorkerResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    employee_code: str
    name: str
    skill: str
    department: str
    shift: str
    production_line_id: int | None
    status: WorkerStatus
    created_by: int | None
    created_at: datetime
    updated_at: datetime


class WorkerBatchAssignment(BaseModel):
    batch_id: int = Field(
        gt=0,
    )