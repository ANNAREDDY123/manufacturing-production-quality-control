from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.machine_maintenance import (
    MaintenanceStatus,
    MaintenanceType,
)


class MachineMaintenanceCreate(BaseModel):
    maintenance_number: str = Field(
        min_length=2,
        max_length=50,
    )

    machine_id: int = Field(gt=0)

    maintenance_type: MaintenanceType

    scheduled_date: datetime

    technician_id: int | None = Field(
        default=None,
        gt=0,
    )

    description: str = Field(
        min_length=2,
        max_length=5000,
    )

    findings: str | None = None

    actions_taken: str | None = None

    spare_parts_used: str | None = None

    maintenance_cost: float = Field(
        default=0,
        ge=0,
    )

    downtime_hours: float = Field(
        default=0,
        ge=0,
    )

    remarks: str | None = None


class MachineMaintenanceUpdate(BaseModel):
    maintenance_type: MaintenanceType | None = None

    scheduled_date: datetime | None = None

    technician_id: int | None = Field(
        default=None,
        gt=0,
    )

    description: str | None = Field(
        default=None,
        min_length=2,
        max_length=5000,
    )

    findings: str | None = None

    actions_taken: str | None = None

    spare_parts_used: str | None = None

    maintenance_cost: float | None = Field(
        default=None,
        ge=0,
    )

    downtime_hours: float | None = Field(
        default=None,
        ge=0,
    )

    remarks: str | None = None


class MachineMaintenanceStatusUpdate(BaseModel):
    status: MaintenanceStatus


class MachineMaintenanceResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    maintenance_number: str
    machine_id: int
    maintenance_type: MaintenanceType
    status: MaintenanceStatus
    scheduled_date: datetime
    started_at: datetime | None
    completed_at: datetime | None
    technician_id: int | None
    description: str
    findings: str | None
    actions_taken: str | None
    spare_parts_used: str | None
    maintenance_cost: float
    downtime_hours: float
    remarks: str | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime