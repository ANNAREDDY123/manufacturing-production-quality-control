import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.machine_maintenance import (
    MaintenanceStatus,
    MaintenanceType,
)
from app.schemas.machine_maintenance import (
    MachineMaintenanceCreate,
    MachineMaintenanceUpdate,
)


def unique_number(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_maintenance_create_schema_valid():
    data = MachineMaintenanceCreate(
        maintenance_number=unique_number("MNT"),
        machine_id=1,
        maintenance_type=MaintenanceType.PREVENTIVE,
        scheduled_date=datetime(2026, 10, 10, 10, 0),
        technician_id=1,
        description="Routine preventive maintenance",
        maintenance_cost=2500,
        downtime_hours=2,
    )

    assert data.machine_id == 1
    assert data.maintenance_type == MaintenanceType.PREVENTIVE
    assert data.maintenance_cost == 2500
    assert data.downtime_hours == 2


def test_maintenance_schema_rejects_invalid_machine():
    with pytest.raises(ValidationError):
        MachineMaintenanceCreate(
            maintenance_number=unique_number("MNT"),
            machine_id=0,
            maintenance_type=MaintenanceType.PREVENTIVE,
            scheduled_date=datetime(2026, 10, 10, 10, 0),
            description="Routine maintenance",
        )


def test_maintenance_schema_rejects_negative_cost():
    with pytest.raises(ValidationError):
        MachineMaintenanceCreate(
            maintenance_number=unique_number("MNT"),
            machine_id=1,
            maintenance_type=MaintenanceType.CORRECTIVE,
            scheduled_date=datetime(2026, 10, 10, 10, 0),
            description="Corrective maintenance",
            maintenance_cost=-100,
        )


def test_maintenance_schema_rejects_negative_downtime():
    with pytest.raises(ValidationError):
        MachineMaintenanceCreate(
            maintenance_number=unique_number("MNT"),
            machine_id=1,
            maintenance_type=MaintenanceType.CORRECTIVE,
            scheduled_date=datetime(2026, 10, 10, 10, 0),
            description="Corrective maintenance",
            downtime_hours=-1,
        )


def test_maintenance_update_schema_valid():
    data = MachineMaintenanceUpdate(
        maintenance_type=MaintenanceType.EMERGENCY,
        maintenance_cost=5000,
        downtime_hours=4,
        findings="Bearing damaged",
    )

    assert data.maintenance_type == MaintenanceType.EMERGENCY
    assert data.maintenance_cost == 5000
    assert data.downtime_hours == 4


def test_maintenance_status_values():
    assert MaintenanceStatus.SCHEDULED.value == "Scheduled"
    assert MaintenanceStatus.IN_PROGRESS.value == "In Progress"
    assert MaintenanceStatus.COMPLETED.value == "Completed"
    assert MaintenanceStatus.CANCELLED.value == "Cancelled"


def test_maintenance_type_values():
    assert MaintenanceType.PREVENTIVE.value == "Preventive"
    assert MaintenanceType.CORRECTIVE.value == "Corrective"
    assert MaintenanceType.EMERGENCY.value == "Emergency"