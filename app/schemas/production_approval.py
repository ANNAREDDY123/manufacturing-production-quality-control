from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.production_approval import ProductionApprovalStatus


class ProductionApprovalCreate(BaseModel):
    approval_number: str = Field(
        min_length=2,
        max_length=50,
    )

    production_batch_id: int | None = Field(
        default=None,
        gt=0,
    )

    production_order_id: int | None = Field(
        default=None,
        gt=0,
    )

    requested_by: int = Field(
        gt=0,
    )

    remarks: str | None = None

    @model_validator(mode="after")
    def validate_linkage(self):
        if (
            self.production_batch_id is None
            and self.production_order_id is None
        ):
            raise ValueError(
                "Either production_batch_id or "
                "production_order_id must be provided"
            )

        return self


class ProductionApprovalUpdate(BaseModel):
    remarks: str | None = None


class ProductionApprovalStatusUpdate(BaseModel):
    status: ProductionApprovalStatus

    approver_id: int | None = Field(
        default=None,
        gt=0,
    )

    remarks: str | None = None

    rejection_reason: str | None = None


class ProductionApprovalResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    approval_number: str
    production_batch_id: int | None
    production_order_id: int | None
    status: ProductionApprovalStatus
    requested_by: int
    requested_at: datetime
    approved_by: int | None
    approved_at: datetime | None
    rejected_by: int | None
    rejected_at: datetime | None
    remarks: str | None
    rejection_reason: str | None
    created_at: datetime
    updated_at: datetime