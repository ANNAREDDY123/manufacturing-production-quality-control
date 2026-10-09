from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.quality_inspection import QualityInspectionStatus


class QualityInspectionCreate(BaseModel):
    inspection_number: str = Field(
        min_length=2,
        max_length=50,
    )

    production_batch_id: int = Field(
        gt=0,
    )

    inspector_id: int = Field(
        gt=0,
    )

    inspection_date: datetime | None = None

    sample_quantity: float = Field(
        gt=0,
    )

    accepted_quantity: float = Field(
        ge=0,
        default=0,
    )

    rejected_quantity: float = Field(
        ge=0,
        default=0,
    )

    remarks: str | None = None

    @model_validator(mode="after")
    def validate_quantities(self):
        if (
            self.accepted_quantity + self.rejected_quantity
            > self.sample_quantity
        ):
            raise ValueError(
                "Accepted and rejected quantities cannot exceed sample quantity"
            )

        return self


class QualityInspectionUpdate(BaseModel):
    inspector_id: int | None = Field(
        default=None,
        gt=0,
    )

    inspection_date: datetime | None = None

    sample_quantity: float | None = Field(
        default=None,
        gt=0,
    )

    accepted_quantity: float | None = Field(
        default=None,
        ge=0,
    )

    rejected_quantity: float | None = Field(
        default=None,
        ge=0,
    )

    remarks: str | None = None

    @model_validator(mode="after")
    def validate_quantities(self):
        values = self.model_dump(exclude_unset=True)

        sample = values.get("sample_quantity")
        accepted = values.get("accepted_quantity")
        rejected = values.get("rejected_quantity")

        if (
            sample is not None
            and accepted is not None
            and rejected is not None
            and accepted + rejected > sample
        ):
            raise ValueError(
                "Accepted and rejected quantities cannot exceed sample quantity"
            )

        return self


class QualityInspectionStatusUpdate(BaseModel):
    status: QualityInspectionStatus


class QualityInspectionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    inspection_number: str
    production_batch_id: int
    inspector_id: int
    inspection_date: datetime
    sample_quantity: float
    accepted_quantity: float
    rejected_quantity: float
    status: QualityInspectionStatus
    remarks: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime
    acceptance_percentage: float
    rejection_percentage: float