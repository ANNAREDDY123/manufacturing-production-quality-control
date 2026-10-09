from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.production_line import ProductionLine
from app.models.production_batch import ProductionBatch
from app.models.shift import Shift, ShiftStatus
from app.models.shift_worker import ShiftWorker
from app.models.worker import Worker, WorkerStatus
from app.schemas.shift import (
    ShiftCreate,
    ShiftOutputUpdate,
    ShiftUpdate,
)


def _get_shift(
    db: Session,
    shift_id: int,
) -> Shift:
    shift = db.scalar(
        select(Shift).where(Shift.id == shift_id)
    )

    if shift is None:
        raise ValueError("Shift not found")

    return shift


def _validate_production_line(
    db: Session,
    production_line_id: int | None,
) -> None:
    if production_line_id is None:
        return

    line = db.scalar(
        select(ProductionLine).where(
            ProductionLine.id == production_line_id
        )
    )

    if line is None:
        raise ValueError("Production line not found")


def _validate_supervisor(
    db: Session,
    supervisor_id: int | None,
) -> None:
    if supervisor_id is None:
        return

    from app.models.user import User

    supervisor = db.scalar(
        select(User).where(User.id == supervisor_id)
    )

    if supervisor is None:
        raise ValueError("Supervisor not found")


def _calculate_performance(
    planned_output: float,
    production_output: float,
    rejected_output: float,
) -> float:
    if planned_output <= 0:
        return 0.0

    completion = (
        production_output / planned_output
    ) * 100

    total_output = production_output + rejected_output

    if total_output > 0:
        quality_factor = (
            production_output / total_output
        )
    else:
        quality_factor = 0

    performance = completion * quality_factor

    return round(
        min(max(performance, 0), 100),
        2,
    )


def create_shift(
    db: Session,
    data: ShiftCreate,
    created_by: int | None = None,
) -> Shift:
    existing = db.scalar(
        select(Shift).where(
            Shift.shift_code == data.shift_code
        )
    )

    if existing is not None:
        raise ValueError(
            "Shift code already exists"
        )

    _validate_production_line(
        db,
        data.production_line_id,
    )

    _validate_supervisor(
        db,
        data.supervisor_id,
    )

    shift = Shift(
        **data.model_dump(),
        created_by=created_by,
    )

    db.add(shift)
    db.commit()
    db.refresh(shift)

    return shift


def get_shift(
    db: Session,
    shift_id: int,
) -> Shift:
    return _get_shift(db, shift_id)


def list_shifts(
    db: Session,
    shift_type=None,
    shift_date=None,
    production_line_id=None,
    status=None,
    skip: int = 0,
    limit: int = 100,
):
    statement = select(Shift)

    if shift_type is not None:
        statement = statement.where(
            Shift.shift_type == shift_type
        )

    if shift_date is not None:
        statement = statement.where(
            Shift.shift_date == shift_date
        )

    if production_line_id is not None:
        statement = statement.where(
            Shift.production_line_id
            == production_line_id
        )

    if status is not None:
        statement = statement.where(
            Shift.status == status
        )

    statement = (
        statement
        .order_by(Shift.shift_date.desc(), Shift.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def update_shift(
    db: Session,
    shift_id: int,
    data: ShiftUpdate,
) -> Shift:
    shift = _get_shift(db, shift_id)

    if shift.status == ShiftStatus.COMPLETED:
        raise ValueError(
            "Completed shifts cannot be updated"
        )

    if shift.status == ShiftStatus.CANCELLED:
        raise ValueError(
            "Cancelled shifts cannot be updated"
        )

    if data.production_line_id is not None:
        _validate_production_line(
            db,
            data.production_line_id,
        )

    if data.supervisor_id is not None:
        _validate_supervisor(
            db,
            data.supervisor_id,
        )

    values = data.model_dump(
        exclude_unset=True,
    )

    for field, value in values.items():
        setattr(shift, field, value)

    db.commit()
    db.refresh(shift)

    return shift


def update_shift_status(
    db: Session,
    shift_id: int,
    status: ShiftStatus,
) -> Shift:
    shift = _get_shift(db, shift_id)

    current = shift.status

    if current == ShiftStatus.COMPLETED:
        raise ValueError(
            "Completed shifts are terminal"
        )

    if current == ShiftStatus.CANCELLED:
        raise ValueError(
            "Cancelled shifts are terminal"
        )

    allowed = {
        ShiftStatus.PLANNED: {
            ShiftStatus.ACTIVE,
            ShiftStatus.CANCELLED,
        },
        ShiftStatus.ACTIVE: {
            ShiftStatus.COMPLETED,
            ShiftStatus.CANCELLED,
        },
    }

    if (
        status != current
        and status not in allowed.get(current, set())
    ):
        raise ValueError(
            f"Cannot transition shift from "
            f"{current.value} to {status.value}"
        )

    now = datetime.utcnow()

    if status == ShiftStatus.ACTIVE:
        shift.actual_start = now

    if status == ShiftStatus.COMPLETED:
        shift.actual_end = now

    shift.status = status

    db.commit()
    db.refresh(shift)

    return shift


def update_shift_output(
    db: Session,
    shift_id: int,
    data: ShiftOutputUpdate,
) -> Shift:
    shift = _get_shift(db, shift_id)

    if shift.status == ShiftStatus.COMPLETED:
        raise ValueError(
            "Completed shifts cannot record output"
        )

    if shift.status == ShiftStatus.CANCELLED:
        raise ValueError(
            "Cancelled shifts cannot record output"
        )

    shift.production_output = data.production_output
    shift.rejected_output = data.rejected_output
    shift.machine_usage_hours = (
        data.machine_usage_hours
    )

    shift.performance_percentage = (
        _calculate_performance(
            shift.planned_output,
            shift.production_output,
            shift.rejected_output,
        )
    )

    db.commit()
    db.refresh(shift)

    return shift


def get_shift_metrics(
    db: Session,
    shift_id: int,
):
    shift = _get_shift(db, shift_id)

    return {
        "shift_id": shift.id,
        "planned_output": shift.planned_output,
        "production_output": shift.production_output,
        "rejected_output": shift.rejected_output,
        "machine_usage_hours": shift.machine_usage_hours,
        "completion_percentage": (
            shift.completion_percentage
        ),
        "rejection_percentage": (
            shift.rejection_percentage
        ),
        "performance_percentage": (
            shift.performance_percentage
        ),
    }


def assign_worker(
    db: Session,
    shift_id: int,
    worker_id: int,
):
    shift = _get_shift(db, shift_id)

    if shift.status in {
        ShiftStatus.COMPLETED,
        ShiftStatus.CANCELLED,
    }:
        raise ValueError(
            "Workers cannot be assigned to a "
            "completed or cancelled shift"
        )

    worker = db.scalar(
        select(Worker).where(
            Worker.id == worker_id
        )
    )

    if worker is None:
        raise ValueError("Worker not found")

    if worker.status != WorkerStatus.ACTIVE:
        raise ValueError(
            "Only active workers can be assigned "
            "to shifts"
        )

    existing = db.scalar(
        select(ShiftWorker).where(
            ShiftWorker.shift_id == shift_id,
            ShiftWorker.worker_id == worker_id,
        )
    )

    if existing is not None:
        raise ValueError(
            "Worker is already assigned to this shift"
        )

    assignment = ShiftWorker(
        shift_id=shift_id,
        worker_id=worker_id,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


def remove_worker(
    db: Session,
    shift_id: int,
    worker_id: int,
) -> None:
    assignment = db.scalar(
        select(ShiftWorker).where(
            ShiftWorker.shift_id == shift_id,
            ShiftWorker.worker_id == worker_id,
        )
    )

    if assignment is None:
        raise ValueError(
            "Worker is not assigned to this shift"
        )

    db.delete(assignment)
    db.commit()


def list_shift_workers(
    db: Session,
    shift_id: int,
):
    _get_shift(db, shift_id)

    statement = (
        select(ShiftWorker)
        .where(ShiftWorker.shift_id == shift_id)
        .order_by(ShiftWorker.id)
    )

    return list(db.scalars(statement).all())


def assign_batch_workers(
    db: Session,
    shift_id: int,
    batch_id: int,
):
    shift = _get_shift(db, shift_id)

    batch = db.scalar(
        select(ProductionBatch).where(
            ProductionBatch.id == batch_id
        )
    )

    if batch is None:
        raise ValueError(
            "Production batch not found"
        )

    assignments = list_shift_workers(
        db,
        shift_id,
    )

    if not assignments:
        raise ValueError(
            "At least one worker must be assigned "
            "to the shift before assigning the batch"
        )

    return assignments