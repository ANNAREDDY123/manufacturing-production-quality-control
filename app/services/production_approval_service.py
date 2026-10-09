from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.production_approval import (
    ProductionApproval,
    ProductionApprovalStatus,
)
from app.models.production_batch import ProductionBatch
from app.models.production_order import ProductionOrder
from app.models.user import User
from app.schemas.production_approval import (
    ProductionApprovalCreate,
    ProductionApprovalStatusUpdate,
    ProductionApprovalUpdate,
)


VALID_TRANSITIONS = {
    ProductionApprovalStatus.PENDING: {
        ProductionApprovalStatus.APPROVED,
        ProductionApprovalStatus.REJECTED,
        ProductionApprovalStatus.CANCELLED,
    },
    ProductionApprovalStatus.APPROVED: set(),
    ProductionApprovalStatus.REJECTED: set(),
    ProductionApprovalStatus.CANCELLED: set(),
}


def _get_approval(
    db: Session,
    approval_id: int,
) -> ProductionApproval:
    approval = db.scalar(
        select(ProductionApproval).where(
            ProductionApproval.id == approval_id
        )
    )

    if approval is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production approval not found",
        )

    return approval


def _get_batch(
    db: Session,
    batch_id: int,
) -> ProductionBatch:
    batch = db.scalar(
        select(ProductionBatch).where(
            ProductionBatch.id == batch_id
        )
    )

    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production batch not found",
        )

    return batch


def _get_order(
    db: Session,
    order_id: int,
) -> ProductionOrder:
    order = db.scalar(
        select(ProductionOrder).where(
            ProductionOrder.id == order_id
        )
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production order not found",
        )

    return order


def _get_user(
    db: Session,
    user_id: int,
) -> User:
    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


def create_production_approval(
    db: Session,
    data: ProductionApprovalCreate,
) -> ProductionApproval:

    existing = db.scalar(
        select(ProductionApproval).where(
            ProductionApproval.approval_number
            == data.approval_number
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approval number already exists",
        )

    batch = None
    order = None

    if data.production_batch_id is not None:
        batch = _get_batch(
            db,
            data.production_batch_id,
        )

    if data.production_order_id is not None:
        order = _get_order(
            db,
            data.production_order_id,
        )

    # If both are supplied, make sure the batch belongs
    # to the specified production order.
    if batch is not None and order is not None:
        if batch.production_order_id != order.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Production batch does not belong "
                    "to the specified production order"
                ),
            )

    _get_user(
        db,
        data.requested_by,
    )

    approval = ProductionApproval(
        approval_number=data.approval_number,
        production_batch_id=data.production_batch_id,
        production_order_id=data.production_order_id,
        status=ProductionApprovalStatus.PENDING,
        requested_by=data.requested_by,
        remarks=data.remarks,
    )

    db.add(approval)
    db.commit()
    db.refresh(approval)

    return approval


def list_production_approvals(
    db: Session,
    production_batch_id: int | None = None,
    production_order_id: int | None = None,
    approval_status: ProductionApprovalStatus | None = None,
):
    query = select(
        ProductionApproval
    ).order_by(
        ProductionApproval.id.desc()
    )

    if production_batch_id is not None:
        query = query.where(
            ProductionApproval.production_batch_id
            == production_batch_id
        )

    if production_order_id is not None:
        query = query.where(
            ProductionApproval.production_order_id
            == production_order_id
        )

    if approval_status is not None:
        query = query.where(
            ProductionApproval.status
            == approval_status
        )

    return list(
        db.scalars(query).all()
    )


def get_production_approval(
    db: Session,
    approval_id: int,
) -> ProductionApproval:
    return _get_approval(
        db,
        approval_id,
    )


def update_production_approval(
    db: Session,
    approval_id: int,
    data: ProductionApprovalUpdate,
) -> ProductionApproval:

    approval = _get_approval(
        db,
        approval_id,
    )

    if approval.status != ProductionApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only pending approvals can be modified"
            ),
        )

    if data.remarks is not None:
        approval.remarks = data.remarks

    db.commit()
    db.refresh(approval)

    return approval


def update_production_approval_status(
    db: Session,
    approval_id: int,
    data: ProductionApprovalStatusUpdate,
) -> ProductionApproval:

    approval = _get_approval(
        db,
        approval_id,
    )

    current_status = approval.status
    new_status = data.status

    if current_status == new_status:
        return approval

    allowed_statuses = VALID_TRANSITIONS.get(
        current_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Approval cannot transition from "
                f"{current_status.value} to "
                f"{new_status.value}"
            ),
        )

    if new_status == ProductionApprovalStatus.APPROVED:
        if data.approver_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Approver ID is required for approval",
            )

        _get_user(
            db,
            data.approver_id,
        )

        approval.status = new_status
        approval.approved_by = data.approver_id
        approval.approved_at = datetime.utcnow()

        if data.remarks is not None:
            approval.remarks = data.remarks

    elif new_status == ProductionApprovalStatus.REJECTED:
        if data.approver_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Approver ID is required for rejection",
            )

        if not data.rejection_reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Rejection reason is required "
                    "when rejecting an approval"
                ),
            )

        _get_user(
            db,
            data.approver_id,
        )

        approval.status = new_status
        approval.rejected_by = data.approver_id
        approval.rejected_at = datetime.utcnow()
        approval.rejection_reason = data.rejection_reason

        if data.remarks is not None:
            approval.remarks = data.remarks

    elif new_status == ProductionApprovalStatus.CANCELLED:
        approval.status = new_status

        if data.remarks is not None:
            approval.remarks = data.remarks

    db.commit()
    db.refresh(approval)

    return approval


def delete_production_approval(
    db: Session,
    approval_id: int,
) -> None:

    approval = _get_approval(
        db,
        approval_id,
    )

    if approval.status not in {
        ProductionApprovalStatus.PENDING,
        ProductionApprovalStatus.CANCELLED,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only pending or cancelled approvals "
                "can be deleted"
            ),
        )

    db.delete(approval)
    db.commit()