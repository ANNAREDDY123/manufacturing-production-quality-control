from datetime import date, time

import pytest

from app.models.shift import ShiftStatus, ShiftType
from app.models.shift_worker import ShiftWorker
from app.schemas.shift import (
    ShiftCreate,
    ShiftOutputUpdate,
)


def test_shift_type_values():
    assert ShiftType.MORNING.value == "Morning"
    assert ShiftType.EVENING.value == "Evening"
    assert ShiftType.NIGHT.value == "Night"


def test_shift_status_values():
    assert ShiftStatus.PLANNED.value == "Planned"
    assert ShiftStatus.ACTIVE.value == "Active"
    assert ShiftStatus.COMPLETED.value == "Completed"
    assert ShiftStatus.CANCELLED.value == "Cancelled"


def test_shift_create_schema():
    shift = ShiftCreate(
        shift_code="SHIFT-001",
        shift_type=ShiftType.MORNING,
        shift_date=date.today(),
        scheduled_start=time(6, 0),
        scheduled_end=time(14, 0),
        planned_output=100,
    )

    assert shift.shift_code == "SHIFT-001"
    assert shift.shift_type == ShiftType.MORNING
    assert shift.planned_output == 100


def test_shift_same_start_end_rejected():
    with pytest.raises(ValueError):
        ShiftCreate(
            shift_code="SHIFT-002",
            shift_type=ShiftType.EVENING,
            shift_date=date.today(),
            scheduled_start=time(14, 0),
            scheduled_end=time(14, 0),
        )


def test_shift_output_schema():
    output = ShiftOutputUpdate(
        production_output=90,
        rejected_output=5,
        machine_usage_hours=7.5,
    )

    assert output.production_output == 90
    assert output.rejected_output == 5
    assert output.machine_usage_hours == 7.5


def test_shift_worker_table_name():
    assert ShiftWorker.__tablename__ == "shift_workers"


def test_shift_worker_required_columns():
    columns = ShiftWorker.__table__.columns.keys()

    assert "id" in columns
    assert "shift_id" in columns
    assert "worker_id" in columns
    assert "assigned_at" in columns