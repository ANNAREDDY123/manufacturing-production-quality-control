from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.production_batch import (
    ProductionBatch,
    ProductionBatchStatus,
)
from app.models.production_order import (
    ProductionOrder,
    ProductionOrderStatus,
)
from app.models.user import User, UserRole
from app.schemas.production_batch import (
    ProductionBatchCreate,
    ProductionBatchStatusUpdate,
    ProductionBatchUpdate,
)


VALID_TRANSITIONS = {
    ProductionBatchStatus.PLANNED: {
        ProductionBatchStatus.IN_PROGRESS,
        ProductionBatchStatus.CANCELLED,
    },
    ProductionBatchStatus.IN_PROGRESS: {
        ProductionBatchStatus.PAUSED,
        ProductionBatchStatus.COMPLETED,
        ProductionBatchStatus.CANCELLED,
    },
    ProductionBatchStatus.PAUSED: {
        ProductionBatchStatus.IN_PROGRESS,
        ProductionBatchStatus.CANCELLED,
    },
    ProductionBatchStatus.COMPLETED: set(),
    ProductionBatchStatus.CANCELLED: set(),
}


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
        raise ValueError("Production batch not found")

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
        raise ValueError("Production order not found")

    if order.status in {
        ProductionOrderStatus.COMPLETED,
        ProductionOrderStatus.CANCELLED,
    }:
        raise ValueError(
            "Cannot create a batch for a completed or cancelled production order"
        )

    return order


def _get_supervisor(
    db: Session,
    supervisor_id: int | None,
) -> User | None:
    if supervisor_id is None:
        return None

    supervisor = db.scalar(
        select(User).where(
            User.id == supervisor_id
        )
    )

    if supervisor is None:
        raise ValueError("Supervisor not found")

    if supervisor.role != UserRole.PRODUCTION_SUPERVISOR:
        raise ValueError(
            "Assigned user must have Production Supervisor role"
        )

    if not supervisor.is_active:
        raise ValueError(
            "Supervisor account is inactive"
        )

    return supervisor


def _get_allocated_quantity(
    db: Session,
    order_id: int,
    exclude_batch_id: int | None = None,
) -> float:
    query = select(
        func.coalesce(
            func.sum(ProductionBatch.quantity),
            0,
        )
    ).where(
        ProductionBatch.production_order_id
        == order_id,
        ProductionBatch.status
        != ProductionBatchStatus.CANCELLED,
    )

    if exclude_batch_id is not None:
        query = query.where(
            ProductionBatch.id != exclude_batch_id
        )

    return float(db.scalar(query) or 0)


def _validate_quantity(
    db: Session,
    order: ProductionOrder,
    quantity: float,
    exclude_batch_id: int | None = None,
) -> None:
    allocated_quantity = _get_allocated_quantity(
        db,
        order.id,
        exclude_batch_id=exclude_batch_id,
    )

    if allocated_quantity + quantity > order.quantity:
        remaining = max(
            order.quantity - allocated_quantity,
            0,
        )

        raise ValueError(
            f"Batch quantity exceeds remaining production order quantity "
            f"({remaining:g})"
        )


def create_production_batch(
    db: Session,
    data: ProductionBatchCreate,
    created_by: int | None = None,
) -> ProductionBatch:
    existing = db.scalar(
        select(ProductionBatch).where(
            ProductionBatch.batch_number
            == data.batch_number
        )
    )

    if existing:
        raise ValueError(
            "Production batch number already exists"
        )

    order = _get_order(
        db,
        data.production_order_id,
    )

    _validate_quantity(
        db,
        order,
        data.quantity,
    )

    _get_supervisor(
        db,
        data.supervisor_id,
    )

    batch = ProductionBatch(
        batch_number=data.batch_number,
        production_order_id=data.production_order_id,
        quantity=data.quantity,
        supervisor_id=data.supervisor_id,
        planned_start=data.planned_start,
        status=ProductionBatchStatus.PLANNED,
        created_by=created_by,
    )

    db.add(batch)
    db.commit()
    db.refresh(batch)

    return batch


def get_production_batch(
    db: Session,
    batch_id: int,
) -> ProductionBatch:
    return _get_batch(
        db,
        batch_id,
    )


def list_production_batches(
    db: Session,
    search: str | None = None,
    production_order_id: int | None = None,
    status: ProductionBatchStatus | None = None,
    supervisor_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[ProductionBatch]:
    query = select(ProductionBatch)

    if search:
        search_value = f"%{search}%"

        query = query.where(
            ProductionBatch.batch_number.ilike(
                search_value
            )
        )

    if production_order_id is not None:
        query = query.where(
            ProductionBatch.production_order_id
            == production_order_id
        )

    if status is not None:
        query = query.where(
            ProductionBatch.status == status
        )

    if supervisor_id is not None:
        query = query.where(
            ProductionBatch.supervisor_id
            == supervisor_id
        )

    query = (
        query
        .order_by(ProductionBatch.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(
        db.scalars(query).all()
    )


def update_production_batch(
    db: Session,
    batch_id: int,
    data: ProductionBatchUpdate,
) -> ProductionBatch:
    batch = _get_batch(
        db,
        batch_id,
    )

    if batch.status not in {
        ProductionBatchStatus.PLANNED,
        ProductionBatchStatus.PAUSED,
    }:
        raise ValueError(
            "Only Planned or Paused batches can be modified"
        )

    if data.quantity is not None:
        order = _get_order(
            db,
            batch.production_order_id,
        )

        _validate_quantity(
            db,
            order,
            data.quantity,
            exclude_batch_id=batch.id,
        )

        batch.quantity = data.quantity

    if data.supervisor_id is not None:
        _get_supervisor(
            db,
            data.supervisor_id,
        )

        batch.supervisor_id = data.supervisor_id

    if data.planned_start is not None:
        batch.planned_start = data.planned_start

    db.commit()
    db.refresh(batch)

    return batch


def update_production_batch_status(
    db: Session,
    batch_id: int,
    data: ProductionBatchStatusUpdate,
) -> ProductionBatch:
    batch = _get_batch(
        db,
        batch_id,
    )

    current_status = batch.status
    new_status = data.status

    if current_status == new_status:
        return batch

    allowed_statuses = VALID_TRANSITIONS.get(
        current_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise ValueError(
            f"Cannot transition batch from "
            f"{current_status.value} to {new_status.value}"
        )

    if new_status == ProductionBatchStatus.IN_PROGRESS:
        if batch.actual_start is None:
            batch.actual_start = datetime.utcnow()

    if new_status == ProductionBatchStatus.COMPLETED:
        if batch.actual_start is None:
            batch.actual_start = datetime.utcnow()

        batch.actual_end = datetime.utcnow()

    if new_status == ProductionBatchStatus.CANCELLED:
        batch.actual_end = None

    batch.status = new_status

    db.commit()
    db.refresh(batch)

    return batch