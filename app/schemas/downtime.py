from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.downtime import DowntimeReason, DowntimeStatus


class DowntimeCreate(BaseModel):
    downtime_number: str = Field(min_length=2, max_length=50)
    machine_id: int = Field(gt=0)
    reason: DowntimeReason
    started_at: datetime
    reported_by: int = Field(gt=0)
    description: str = Field(min_length=2)
    root_cause: str | None = None
    corrective_action: str | None = None
    remarks: str | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        return self


class DowntimeUpdate(BaseModel):
    reason: DowntimeReason | None = None
    started_at: datetime | None = None
    description: str | None = Field(default=None, min_length=2)
    root_cause: str | None = None
    corrective_action: str | None = None
    remarks: str | None = None


class DowntimeStatusUpdate(BaseModel):
    status: DowntimeStatus
    resolved_by: int | None = Field(default=None, gt=0)
    ended_at: datetime | None = None
    corrective_action: str | None = None
    remarks: str | None = None


class DowntimeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    downtime_number: str
    machine_id: int
    reason: DowntimeReason
    status: DowntimeStatus
    started_at: datetime
    ended_at: datetime | None
    duration_hours: float
    reported_by: int
    resolved_by: int | None
    description: str
    root_cause: str | None
    corrective_action: str | None
    remarks: str | None
    created_at: datetime
    updated_at: datetime