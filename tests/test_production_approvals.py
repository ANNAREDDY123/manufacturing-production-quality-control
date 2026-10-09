from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.production_approval import (
    ProductionApprovalStatus,
)
from app.schemas.production_approval import (
    ProductionApprovalCreate,
    ProductionApprovalStatusUpdate,
    ProductionApprovalUpdate,
)


def test_create_approval_for_batch():
    data = ProductionApprovalCreate(
        approval_number="APR-001",
        production_batch_id=1,
        requested_by=1,
        remarks="Ready for production approval",
    )

    assert data.approval_number == "APR-001"
    assert data.production_batch_id == 1
    assert data.production_order_id is None


def test_create_approval_for_order():
    data = ProductionApprovalCreate(
        approval_number="APR-002",
        production_order_id=1,
        requested_by=1,
    )

    assert data.production_order_id == 1
    assert data.production_batch_id is None


def test_approval_requires_batch_or_order():
    with pytest.raises(ValidationError):
        ProductionApprovalCreate(
            approval_number="APR-003",
            requested_by=1,
        )


def test_approval_requires_valid_requester():
    with pytest.raises(ValidationError):
        ProductionApprovalCreate(
            approval_number="APR-004",
            production_batch_id=1,
            requested_by=0,
        )


def test_status_update_schema():
    data = ProductionApprovalStatusUpdate(
        status=ProductionApprovalStatus.APPROVED,
        approver_id=5,
        remarks="Approved for production",
    )

    assert data.status == ProductionApprovalStatus.APPROVED
    assert data.approver_id == 5


def test_rejection_schema():
    data = ProductionApprovalStatusUpdate(
        status=ProductionApprovalStatus.REJECTED,
        approver_id=5,
        rejection_reason="Quality requirements not met",
        remarks="Please correct the issue",
    )

    assert data.status == ProductionApprovalStatus.REJECTED
    assert data.rejection_reason == (
        "Quality requirements not met"
    )


def test_update_schema():
    data = ProductionApprovalUpdate(
        remarks="Updated approval remarks"
    )

    assert data.remarks == "Updated approval remarks"


def test_approval_status_values():
    assert ProductionApprovalStatus.PENDING.value == "Pending"
    assert ProductionApprovalStatus.APPROVED.value == "Approved"
    assert ProductionApprovalStatus.REJECTED.value == "Rejected"
    assert ProductionApprovalStatus.CANCELLED.value == "Cancelled"


def test_approval_transition_definitions():
    from app.services.production_approval_service import (
        VALID_TRANSITIONS,
    )

    assert ProductionApprovalStatus.APPROVED in (
        VALID_TRANSITIONS[
            ProductionApprovalStatus.PENDING
        ]
    )

    assert ProductionApprovalStatus.REJECTED in (
        VALID_TRANSITIONS[
            ProductionApprovalStatus.PENDING
        ]
    )

    assert ProductionApprovalStatus.CANCELLED in (
        VALID_TRANSITIONS[
            ProductionApprovalStatus.PENDING
        ]
    )

    assert (
        VALID_TRANSITIONS[
            ProductionApprovalStatus.APPROVED
        ]
        == set()
    )

    assert (
        VALID_TRANSITIONS[
            ProductionApprovalStatus.REJECTED
        ]
        == set()
    )


def test_approval_update_does_not_require_all_fields():
    data = ProductionApprovalUpdate()

    assert data.remarks is None


def test_approval_create_accepts_both_batch_and_order():
    data = ProductionApprovalCreate(
        approval_number="APR-005",
        production_batch_id=10,
        production_order_id=20,
        requested_by=1,
    )

    assert data.production_batch_id == 10
    assert data.production_order_id == 20