import uuid

import pytest
from pydantic import ValidationError

from app.models.quality_inspection import (
    QualityInspection,
    QualityInspectionStatus,
)
from app.schemas.quality_inspection import (
    QualityInspectionCreate,
    QualityInspectionUpdate,
)


def unique_number(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_create_schema_valid():
    data = QualityInspectionCreate(
        inspection_number=unique_number("QI"),
        production_batch_id=1,
        inspector_id=1,
        sample_quantity=100,
        accepted_quantity=95,
        rejected_quantity=5,
        remarks="Routine inspection",
    )

    assert data.sample_quantity == 100
    assert data.accepted_quantity == 95
    assert data.rejected_quantity == 5


def test_create_schema_rejects_excess_quantity():
    with pytest.raises(ValidationError):
        QualityInspectionCreate(
            inspection_number=unique_number("QI"),
            production_batch_id=1,
            inspector_id=1,
            sample_quantity=100,
            accepted_quantity=80,
            rejected_quantity=30,
        )


def test_create_schema_rejects_negative_quantity():
    with pytest.raises(ValidationError):
        QualityInspectionCreate(
            inspection_number=unique_number("QI"),
            production_batch_id=1,
            inspector_id=1,
            sample_quantity=100,
            accepted_quantity=-1,
            rejected_quantity=0,
        )


def test_update_schema_valid():
    data = QualityInspectionUpdate(
        sample_quantity=100,
        accepted_quantity=90,
        rejected_quantity=10,
    )

    assert data.sample_quantity == 100
    assert data.accepted_quantity == 90
    assert data.rejected_quantity == 10


def test_model_acceptance_percentage():
    class Dummy:
        sample_quantity = 100
        accepted_quantity = 92
        rejected_quantity = 8

    acceptance = QualityInspection.acceptance_percentage.fget(Dummy())
    rejection = QualityInspection.rejection_percentage.fget(Dummy())

    assert acceptance == 92.0
    assert rejection == 8.0


def test_model_zero_sample_percentage():
    class Dummy:
        sample_quantity = 0
        accepted_quantity = 0
        rejected_quantity = 0

    acceptance = QualityInspection.acceptance_percentage.fget(Dummy())
    rejection = QualityInspection.rejection_percentage.fget(Dummy())

    assert acceptance == 0.0
    assert rejection == 0.0


def test_quality_status_values():
    assert QualityInspectionStatus.PENDING.value == "Pending"
    assert QualityInspectionStatus.PASSED.value == "Passed"
    assert QualityInspectionStatus.FAILED.value == "Failed"
    assert QualityInspectionStatus.CANCELLED.value == "Cancelled"