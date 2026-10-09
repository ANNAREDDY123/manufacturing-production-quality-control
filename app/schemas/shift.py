from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.shift import ShiftStatus, ShiftType


class ShiftCreate(BaseModel):
    shift_code: str = Field(
        min_length=2,
        max_length=50,
    )

    shift_type: ShiftType

    shift_date: date

    scheduled_start: time

    scheduled_end: time

    production_line_id: int | None = Field(
        default=None,
        gt=0,
    )

    supervisor_id: int | None = Field(
        default=None,
        gt=0,
    )

    planned_output: float = Field(
        default=0,
        ge=0,
    )

    status: ShiftStatus = ShiftStatus.PLANNED

    @model_validator(mode="after")
    def validate_timing(self):
        if self.scheduled_start == self.scheduled_end:
            raise ValueError(
                "Shift start and end time cannot be the same"
            )

        return self


class ShiftUpdate(BaseModel):
    shift_type: ShiftType | None = None
    shift_date: date | None = None
    scheduled_start: time | None = None
    scheduled_end: time | None = None
    production_line_id: int | None = Field(
        default=None,
        gt=0,
    )
    supervisor_id: int | None = Field(
        default=None,
        gt=0,
    )
    planned_output: float | None = Field(
        default=None,
        ge=0,
    )
    status: ShiftStatus | None = None

    @model_validator(mode="after")
    def validate_timing(self):
        if (
            self.scheduled_start is not None
            and self.scheduled_end is not None
            and self.scheduled_start == self.scheduled_end
        ):
            raise ValueError(
                "Shift start and end time cannot be the same"
            )

        return self


class ShiftOutputUpdate(BaseModel):
    production_output: float = Field(
        ge=0,
    )

    rejected_output: float = Field(
        default=0,
        ge=0,
    )

    machine_usage_hours: float = Field(
        default=0,
        ge=0,
    )


class ShiftStatusUpdate(BaseModel):
    status: ShiftStatus


class ShiftWorkerAssignment(BaseModel):
    worker_id: int = Field(
        gt=0,
    )


class ShiftResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    shift_code: str
    shift_type: ShiftType
    shift_date: date
    scheduled_start: time
    scheduled_end: time
    actual_start: datetime | None
    actual_end: datetime | None
    production_line_id: int | None
    supervisor_id: int | None
    planned_output: float
    production_output: float
    rejected_output: float
    machine_usage_hours: float
    performance_percentage: float
    status: ShiftStatus
    created_by: int | None
    created_at: datetime
    updated_at: datetime


class ShiftMetricsResponse(BaseModel):
    shift_id: int
    planned_output: float
    production_output: float
    rejected_output: float
    machine_usage_hours: float
    completion_percentage: float
    rejection_percentage: float
    performance_percentage: float