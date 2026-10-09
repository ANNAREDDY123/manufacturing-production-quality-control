from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.defect import (
    DefectSeverity,
    DefectStatus,
    DefectType,
)


class DefectCreate(BaseModel):
    defect_number: str = Field(
        min_length=2,
        max_length=50,
    )

    production_batch_id: int = Field(
        gt=0,
    )

    quality_inspection_id: int | None = Field(
        default=None,
        gt=0,
    )

    reported_by: int = Field(
        gt=0,
    )

    defect_type: DefectType

    severity: DefectSeverity = DefectSeverity.MEDIUM

    description: str = Field(
        min_length=2,
        max_length=5000,
    )

    defect_quantity: float = Field(
        gt=0,
    )

    root_cause: str | None = None

    corrective_action: str | None = None

    preventive_action: str | None = None

    remarks: str | None = None


class DefectUpdate(BaseModel):
    defect_type: DefectType | None = None

    severity: DefectSeverity | None = None

    description: str | None = Field(
        default=None,
        min_length=2,
        max_length=5000,
    )

    defect_quantity: float | None = Field(
        default=None,
        gt=0,
    )

    root_cause: str | None = None

    corrective_action: str | None = None

    preventive_action: str | None = None

    remarks: str | None = None


class DefectStatusUpdate(BaseModel):
    status: DefectStatus


class DefectResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    defect_number: str
    production_batch_id: int
    quality_inspection_id: int | None
    reported_by: int
    defect_type: DefectType
    severity: DefectSeverity
    description: str
    defect_quantity: float
    root_cause: str | None
    corrective_action: str | None
    preventive_action: str | None
    status: DefectStatus
    resolved_at: datetime | None
    resolved_by: int | None
    remarks: str | None
    created_at: datetime
    updated_at: datetime