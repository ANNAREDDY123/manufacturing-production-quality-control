import uuid

import pytest
from pydantic import ValidationError

from app.models.defect import (
    DefectSeverity,
    DefectStatus,
    DefectType,
)
from app.schemas.defect import (
    DefectCreate,
    DefectUpdate,
)


def unique_number(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_defect_create_schema_valid():
    data = DefectCreate(
        defect_number=unique_number("DEF"),
        production_batch_id=1,
        quality_inspection_id=1,
        reported_by=1,
        defect_type=DefectType.SURFACE,
        severity=DefectSeverity.HIGH,
        description="Surface scratch detected",
        defect_quantity=5,
        root_cause="Improper handling",
        corrective_action="Rework affected units",
        preventive_action="Improve handling procedure",
        remarks="Quality review required",
    )

    assert data.production_batch_id == 1
    assert data.quality_inspection_id == 1
    assert data.defect_quantity == 5
    assert data.severity == DefectSeverity.HIGH


def test_defect_create_schema_rejects_invalid_batch():
    with pytest.raises(ValidationError):
        DefectCreate(
            defect_number=unique_number("DEF"),
            production_batch_id=0,
            reported_by=1,
            defect_type=DefectType.MATERIAL,
            severity=DefectSeverity.LOW,
            description="Material issue",
            defect_quantity=1,
        )


def test_defect_create_schema_rejects_invalid_quantity():
    with pytest.raises(ValidationError):
        DefectCreate(
            defect_number=unique_number("DEF"),
            production_batch_id=1,
            reported_by=1,
            defect_type=DefectType.MATERIAL,
            severity=DefectSeverity.MEDIUM,
            description="Material issue",
            defect_quantity=0,
        )


def test_defect_create_schema_rejects_empty_description():
    with pytest.raises(ValidationError):
        DefectCreate(
            defect_number=unique_number("DEF"),
            production_batch_id=1,
            reported_by=1,
            defect_type=DefectType.OTHER,
            severity=DefectSeverity.LOW,
            description="",
            defect_quantity=1,
        )


def test_defect_update_schema_valid():
    data = DefectUpdate(
        severity=DefectSeverity.CRITICAL,
        defect_quantity=10,
        corrective_action="Immediate corrective action",
    )

    assert data.severity == DefectSeverity.CRITICAL
    assert data.defect_quantity == 10


def test_defect_status_values():
    assert DefectStatus.OPEN.value == "Open"
    assert DefectStatus.UNDER_REVIEW.value == "Under Review"
    assert DefectStatus.CORRECTIVE_ACTION.value == "Corrective Action"
    assert DefectStatus.RESOLVED.value == "Resolved"
    assert DefectStatus.CLOSED.value == "Closed"
    assert DefectStatus.REJECTED.value == "Rejected"


def test_defect_severity_values():
    assert DefectSeverity.LOW.value == "Low"
    assert DefectSeverity.MEDIUM.value == "Medium"
    assert DefectSeverity.HIGH.value == "High"
    assert DefectSeverity.CRITICAL.value == "Critical"


def test_defect_type_values():
    assert DefectType.MATERIAL.value == "Material"
    assert DefectType.DIMENSIONAL.value == "Dimensional"
    assert DefectType.SURFACE.value == "Surface"
    assert DefectType.FUNCTIONAL.value == "Functional"
    assert DefectType.ASSEMBLY.value == "Assembly"
    assert DefectType.PROCESS.value == "Process"
    assert DefectType.MACHINE.value == "Machine"
    assert DefectType.OTHER.value == "Other"