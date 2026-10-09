from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.production_batch import ProductionBatch
from app.models.production_batch_worker import (
    ProductionBatchWorker,
)
from app.models.production_line import ProductionLine
from app.models.worker import Worker, WorkerStatus
from app.schemas.worker import (
    WorkerCreate,
    WorkerStatusUpdate,
    WorkerUpdate,
)


def _get_worker(
    db: Session,
    worker_id: int,
) -> Worker:
    worker = db.scalar(
        select(Worker).where(
            Worker.id == worker_id
        )
    )

    if worker is None:
        raise ValueError("Worker not found")

    return worker


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
        raise ValueError(
            "Production line not found"
        )


def create_worker(
    db: Session,
    data: WorkerCreate,
    created_by: int | None = None,
) -> Worker:
    existing = db.scalar(
        select(Worker).where(
            Worker.employee_code
            == data.employee_code
        )
    )

    if existing is not None:
        raise ValueError(
            "Worker employee code already exists"
        )

    _validate_production_line(
        db,
        data.production_line_id,
    )

    worker = Worker(
        employee_code=data.employee_code,
        name=data.name,
        skill=data.skill,
        department=data.department,
        shift=data.shift,
        production_line_id=data.production_line_id,
        status=data.status,
        created_by=created_by,
    )

    db.add(worker)
    db.commit()
    db.refresh(worker)

    return worker


def get_worker(
    db: Session,
    worker_id: int,
) -> Worker:
    return _get_worker(
        db,
        worker_id,
    )


def list_workers(
    db: Session,
    search: str | None = None,
    skill: str | None = None,
    department: str | None = None,
    shift: str | None = None,
    production_line_id: int | None = None,
    status: WorkerStatus | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Worker]:
    query = select(Worker)

    if search:
        search_value = f"%{search}%"

        query = query.where(
            or_(
                Worker.employee_code.ilike(
                    search_value
                ),
                Worker.name.ilike(
                    search_value
                ),
                Worker.skill.ilike(
                    search_value
                ),
            )
        )

    if skill is not None:
        query = query.where(
            Worker.skill == skill
        )

    if department is not None:
        query = query.where(
            Worker.department == department
        )

    if shift is not None:
        query = query.where(
            Worker.shift == shift
        )

    if production_line_id is not None:
        query = query.where(
            Worker.production_line_id
            == production_line_id
        )

    if status is not None:
        query = query.where(
            Worker.status == status
        )

    query = (
        query
        .order_by(Worker.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(
        db.scalars(query).all()
    )


def update_worker(
    db: Session,
    worker_id: int,
    data: WorkerUpdate,
) -> Worker:
    worker = _get_worker(
        db,
        worker_id,
    )

    _validate_production_line(
        db,
        data.production_line_id,
    )

    values = data.model_dump(
        exclude_unset=True
    )

    for field, value in values.items():
        setattr(
            worker,
            field,
            value,
        )

    db.commit()
    db.refresh(worker)

    return worker


def update_worker_status(
    db: Session,
    worker_id: int,
    data: WorkerStatusUpdate,
) -> Worker:
    worker = _get_worker(
        db,
        worker_id,
    )

    worker.status = data.status

    db.commit()
    db.refresh(worker)

    return worker


def assign_worker_to_batch(
    db: Session,
    worker_id: int,
    batch_id: int,
) -> ProductionBatchWorker:
    worker = _get_worker(
        db,
        worker_id,
    )

    if worker.status != WorkerStatus.ACTIVE:
        raise ValueError(
            "Only active workers can be assigned "
            "to production batches"
        )

    batch = db.scalar(
        select(ProductionBatch).where(
            ProductionBatch.id == batch_id
        )
    )

    if batch is None:
        raise ValueError(
            "Production batch not found"
        )

    if batch.status.value in {
        "Completed",
        "Cancelled",
    }:
        raise ValueError(
            "Workers cannot be assigned to a "
            "completed or cancelled batch"
        )

    existing = db.scalar(
        select(ProductionBatchWorker).where(
            ProductionBatchWorker.batch_id
            == batch_id,
            ProductionBatchWorker.worker_id
            == worker_id,
        )
    )

    if existing is not None:
        raise ValueError(
            "Worker is already assigned to "
            "this production batch"
        )

    assignment = ProductionBatchWorker(
        batch_id=batch_id,
        worker_id=worker_id,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


def remove_worker_from_batch(
    db: Session,
    worker_id: int,
    batch_id: int,
) -> None:
    assignment = db.scalar(
        select(ProductionBatchWorker).where(
            ProductionBatchWorker.batch_id
            == batch_id,
            ProductionBatchWorker.worker_id
            == worker_id,
        )
    )

    if assignment is None:
        raise ValueError(
            "Worker is not assigned to "
            "this production batch"
        )

    db.delete(assignment)
    db.commit()