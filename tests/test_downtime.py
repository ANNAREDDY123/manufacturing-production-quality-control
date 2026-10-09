from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models.downtime import (
    DowntimeReason,
    DowntimeStatus,
)
from app.schemas.downtime import (
    DowntimeCreate,
    DowntimeStatusUpdate,
    DowntimeUpdate,
)


def test_downtime_create_schema():
    data = DowntimeCreate(
        downtime_number="DT-001",
        machine_id=1,
        reason=DowntimeReason.MACHINE_BREAKDOWN,
        started_at=datetime.utcnow(),
        reported_by=1,
        description="Machine stopped unexpectedly",
    )

    assert data.downtime_number == "DT-001"
    assert data.machine_id == 1
    assert data.reason == DowntimeReason.MACHINE_BREAKDOWN


def test_downtime_invalid_machine():
    with pytest.raises(ValidationError):
        DowntimeCreate(
            downtime_number="DT-002",
            machine_id=0,
            reason=DowntimeReason.MAINTENANCE,
            started_at=datetime.utcnow(),
            reported_by=1,
            description="Maintenance downtime",
        )


def test_downtime_negative_user():
    with pytest.raises(ValidationError):
        DowntimeCreate(
            downtime_number="DT-003",
            machine_id=1,
            reason=DowntimeReason.MAINTENANCE,
            started_at=datetime.utcnow(),
            reported_by=0,
            description="Maintenance downtime",
        )


def test_downtime_description_required():
    with pytest.raises(ValidationError):
        DowntimeCreate(
            downtime_number="DT-004",
            machine_id=1,
            reason=DowntimeReason.OTHER,
            started_at=datetime.utcnow(),
            reported_by=1,
            description="",
        )


def test_downtime_update_schema():
    data = DowntimeUpdate(
        reason=DowntimeReason.QUALITY_ISSUE,
        description="Quality issue identified",
        corrective_action="Inspection performed",
    )

    assert data.reason == DowntimeReason.QUALITY_ISSUE
    assert data.corrective_action == "Inspection performed"


def test_downtime_status_schema():
    data = DowntimeStatusUpdate(
        status=DowntimeStatus.RESOLVED,
        resolved_by=1,
        ended_at=datetime.utcnow(),
        corrective_action="Machine repaired",
    )

    assert data.status == DowntimeStatus.RESOLVED
    assert data.resolved_by == 1


def test_downtime_enum_values():
    assert DowntimeReason.MACHINE_BREAKDOWN.value == "Machine Breakdown"
    assert DowntimeReason.MATERIAL_SHORTAGE.value == "Material Shortage"
    assert DowntimeReason.POWER_FAILURE.value == "Power Failure"
    assert DowntimeReason.QUALITY_ISSUE.value == "Quality Issue"


def test_downtime_status_values():
    assert DowntimeStatus.OPEN.value == "Open"
    assert DowntimeStatus.IN_PROGRESS.value == "In Progress"
    assert DowntimeStatus.RESOLVED.value == "Resolved"
    assert DowntimeStatus.CANCELLED.value == "Cancelled"