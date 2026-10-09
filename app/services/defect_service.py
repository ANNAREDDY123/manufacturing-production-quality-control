from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.defect import (
    Defect,
    DefectStatus,
)
from app.models.production_batch import ProductionBatch
from app.models.quality_inspection import QualityInspection
from app.models.user import User
from app.schemas.defect import (
    DefectCreate,
    DefectStatusUpdate,
    DefectUpdate,
)


def _get_defect(
    db: Session,
    defect_id: int,
) -> Defect:
    defect = db.scalar(
        select(Defect).where(
            Defect.id == defect_id
        )
    )

    if defect is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Defect not found",
        )

    return defect


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


def _validate_inspection(
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


def _validate_user(
    db: Session,
    user_id: int,
    field_name: str = "User",
) -> User:
    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{field_name} not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} account is inactive",
        )

    return user


def create_defect(
    db: Session,
    data: DefectCreate,
    created_by: int,
) -> Defect:

    existing = db.scalar(
        select(Defect).where(
            Defect.defect_number == data.defect_number
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Defect number already exists",
        )

    _validate_batch(
        db,
        data.production_batch_id,
    )

    if data.quality_inspection_id is not None:
        _validate_inspection(
            db,
            data.quality_inspection_id,
        )

    _validate_user(
        db,
        data.reported_by,
        "Reporter",
    )

    defect = Defect(
        defect_number=data.defect_number,
        production_batch_id=data.production_batch_id,
        quality_inspection_id=data.quality_inspection_id,
        reported_by=data.reported_by,
        defect_type=data.defect_type,
        severity=data.severity,
        description=data.description,
        defect_quantity=data.defect_quantity,
        root_cause=data.root_cause,
        corrective_action=data.corrective_action,
        preventive_action=data.preventive_action,
        remarks=data.remarks,
        status=DefectStatus.OPEN,
    )

    db.add(defect)
    db.commit()
    db.refresh(defect)

    return defect


def get_defect(
    db: Session,
    defect_id: int,
) -> Defect:
    return _get_defect(
        db,
        defect_id,
    )


def list_defects(
    db: Session,
    production_batch_id: int | None = None,
    quality_inspection_id: int | None = None,
    severity=None,
    defect_status=None,
    defect_type=None,
) -> list[Defect]:

    query = select(Defect)

    if production_batch_id is not None:
        query = query.where(
            Defect.production_batch_id
            == production_batch_id
        )

    if quality_inspection_id is not None:
        query = query.where(
            Defect.quality_inspection_id
            == quality_inspection_id
        )

    if severity is not None:
        query = query.where(
            Defect.severity == severity
        )

    if defect_status is not None:
        query = query.where(
            Defect.status == defect_status
        )

    if defect_type is not None:
        query = query.where(
            Defect.defect_type == defect_type
        )

    query = query.order_by(
        Defect.id.desc()
    )

    return list(
        db.scalars(query).all()
    )


def update_defect(
    db: Session,
    defect_id: int,
    data: DefectUpdate,
) -> Defect:

    defect = _get_defect(
        db,
        defect_id,
    )

    if defect.status in (
        DefectStatus.RESOLVED,
        DefectStatus.CLOSED,
        DefectStatus.REJECTED,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only open defects can be updated",
        )

    values = data.model_dump(
        exclude_unset=True
    )

    for field, value in values.items():
        setattr(
            defect,
            field,
            value,
        )

    db.commit()
    db.refresh(defect)

    return defect


def update_defect_status(
    db: Session,
    defect_id: int,
    data: DefectStatusUpdate,
    resolved_by: int,
) -> Defect:

    defect = _get_defect(
        db,
        defect_id,
    )

    new_status = data.status

    if defect.status in (
        DefectStatus.CLOSED,
        DefectStatus.REJECTED,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Defect is already in a terminal state",
        )

    if (
        defect.status == DefectStatus.RESOLVED
        and new_status != DefectStatus.CLOSED
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resolved defects can only be closed",
        )

    if new_status == DefectStatus.RESOLVED:
        _validate_user(
            db,
            resolved_by,
            "Resolver",
        )

        defect.resolved_at = datetime.utcnow()
        defect.resolved_by = resolved_by

    elif new_status == DefectStatus.CLOSED:
        if defect.resolved_at is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Defect must be resolved before closing",
            )

    defect.status = new_status

    db.commit()
    db.refresh(defect)

    return defect


def delete_defect(
    db: Session,
    defect_id: int,
) -> None:

    defect = _get_defect(
        db,
        defect_id,
    )

    if defect.status not in (
        DefectStatus.OPEN,
        DefectStatus.REJECTED,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only open or rejected defects can be deleted",
        )

    db.delete(defect)
    db.commit()