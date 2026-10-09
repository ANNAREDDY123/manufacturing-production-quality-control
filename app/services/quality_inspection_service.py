from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.production_batch import ProductionBatch
from app.models.quality_inspection import (
    QualityInspection,
    QualityInspectionStatus,
)
from app.models.user import User
from app.schemas.quality_inspection import (
    QualityInspectionCreate,
    QualityInspectionStatusUpdate,
    QualityInspectionUpdate,
)


def _get_inspection(
    db: Session,
    inspection_id: int,
) -> QualityInspection:
    inspection = db.scalar(
        select(QualityInspection).where(
            QualityInspection.id == inspection_id
        )
    )

    if inspection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quality inspection not found",
        )

    return inspection


def _validate_batch(
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


def _validate_user(
    db: Session,
    user_id: int,
) -> User:
    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspector not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inspector account is inactive",
        )

    return user


def _validate_quantities(
    sample_quantity: float,
    accepted_quantity: float,
    rejected_quantity: float,
) -> None:
    if sample_quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sample quantity must be greater than zero",
        )

    if accepted_quantity < 0 or rejected_quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Accepted and rejected quantities cannot be negative",
        )

    if accepted_quantity + rejected_quantity > sample_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Accepted and rejected quantities cannot "
                "exceed sample quantity"
            ),
        )


def create_inspection(
    db: Session,
    data: QualityInspectionCreate,
    created_by: int,
) -> QualityInspection:
    existing = db.scalar(
        select(QualityInspection).where(
            QualityInspection.inspection_number
            == data.inspection_number
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inspection number already exists",
        )

    _validate_batch(
        db,
        data.production_batch_id,
    )

    _validate_user(
        db,
        data.inspector_id,
    )

    _validate_quantities(
        data.sample_quantity,
        data.accepted_quantity,
        data.rejected_quantity,
    )

    inspection = QualityInspection(
        inspection_number=data.inspection_number,
        production_batch_id=data.production_batch_id,
        inspector_id=data.inspector_id,
        inspection_date=data.inspection_date or datetime.utcnow(),
        sample_quantity=data.sample_quantity,
        accepted_quantity=data.accepted_quantity,
        rejected_quantity=data.rejected_quantity,
        status=QualityInspectionStatus.PENDING,
        remarks=data.remarks,
        created_by=created_by,
    )

    db.add(inspection)
    db.commit()
    db.refresh(inspection)

    return inspection


def get_inspection(
    db: Session,
    inspection_id: int,
) -> QualityInspection:
    return _get_inspection(
        db,
        inspection_id,
    )


def list_inspections(
    db: Session,
    production_batch_id: int | None = None,
    inspector_id: int | None = None,
    inspection_status: QualityInspectionStatus | None = None,
) -> list[QualityInspection]:
    query = select(QualityInspection)

    if production_batch_id is not None:
        query = query.where(
            QualityInspection.production_batch_id
            == production_batch_id
        )

    if inspector_id is not None:
        query = query.where(
            QualityInspection.inspector_id == inspector_id
        )

    if inspection_status is not None:
        query = query.where(
            QualityInspection.status == inspection_status
        )

    query = query.order_by(
        QualityInspection.id.desc()
    )

    return list(db.scalars(query).all())


def update_inspection(
    db: Session,
    inspection_id: int,
    data: QualityInspectionUpdate,
) -> QualityInspection:
    inspection = _get_inspection(
        db,
        inspection_id,
    )

    if inspection.status != QualityInspectionStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending inspections can be updated",
        )

    values = data.model_dump(
        exclude_unset=True,
    )

    new_sample = values.get(
        "sample_quantity",
        inspection.sample_quantity,
    )

    new_accepted = values.get(
        "accepted_quantity",
        inspection.accepted_quantity,
    )

    new_rejected = values.get(
        "rejected_quantity",
        inspection.rejected_quantity,
    )

    _validate_quantities(
        new_sample,
        new_accepted,
        new_rejected,
    )

    if "inspector_id" in values:
        _validate_user(
            db,
            values["inspector_id"],
        )

    for field, value in values.items():
        setattr(
            inspection,
            field,
            value,
        )

    db.commit()
    db.refresh(inspection)

    return inspection


def update_inspection_status(
    db: Session,
    inspection_id: int,
    data: QualityInspectionStatusUpdate,
) -> QualityInspection:
    inspection = _get_inspection(
        db,
        inspection_id,
    )

    if inspection.status != QualityInspectionStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quality inspection is already in a terminal state",
        )

    if data.status == QualityInspectionStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inspection is already pending",
        )

    if data.status == QualityInspectionStatus.PASSED:
        if inspection.accepted_quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A passed inspection must have accepted quantity",
            )

    if data.status == QualityInspectionStatus.FAILED:
        if inspection.rejected_quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A failed inspection must have rejected quantity",
            )

    inspection.status = data.status

    db.commit()
    db.refresh(inspection)

    return inspection


def delete_inspection(
    db: Session,
    inspection_id: int,
) -> None:
    inspection = _get_inspection(
        db,
        inspection_id,
    )

    if inspection.status != QualityInspectionStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending inspections can be deleted",
        )

    db.delete(inspection)
    db.commit()