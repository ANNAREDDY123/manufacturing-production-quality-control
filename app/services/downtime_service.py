from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.downtime import (
    DowntimeStatus,
    MachineDowntime,
)
from app.models.machine import Machine
from app.models.user import User
from app.schemas.downtime import (
    DowntimeCreate,
    DowntimeStatusUpdate,
    DowntimeUpdate,
)


def _get_downtime(
    db: Session,
    downtime_id: int,
) -> MachineDowntime:
    downtime = db.scalar(
        select(MachineDowntime).where(
            MachineDowntime.id == downtime_id
        )
    )

    if downtime is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Downtime record not found",
        )

    return downtime


def _validate_machine(
    db: Session,
    machine_id: int,
) -> Machine:
    machine = db.scalar(
        select(Machine).where(
            Machine.id == machine_id
        )
    )

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return machine


def _validate_user(
    db: Session,
    user_id: int,
    field_name: str,
) -> User:
    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{field_name} user not found",
        )

    return user


def _calculate_duration(
    started_at: datetime,
    ended_at: datetime,
) -> float:
    seconds = (ended_at - started_at).total_seconds()

    if seconds < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ended time cannot be before started time",
        )

    return round(seconds / 3600, 2)


def create_downtime(
    db: Session,
    data: DowntimeCreate,
) -> MachineDowntime:

    existing = db.scalar(
        select(MachineDowntime).where(
            MachineDowntime.downtime_number
            == data.downtime_number
        )
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Downtime number already exists",
        )

    _validate_machine(db, data.machine_id)

    _validate_user(
        db,
        data.reported_by,
        "Reported by",
    )

    downtime = MachineDowntime(
        downtime_number=data.downtime_number,
        machine_id=data.machine_id,
        reason=data.reason,
        status=DowntimeStatus.OPEN,
        started_at=data.started_at,
        reported_by=data.reported_by,
        description=data.description,
        root_cause=data.root_cause,
        corrective_action=data.corrective_action,
        remarks=data.remarks,
    )

    db.add(downtime)
    db.commit()
    db.refresh(downtime)

    return downtime


def list_downtimes(
    db: Session,
    machine_id: int | None = None,
    status_value: DowntimeStatus | None = None,
):
    query = select(MachineDowntime).order_by(
        MachineDowntime.id.desc()
    )

    if machine_id is not None:
        query = query.where(
            MachineDowntime.machine_id == machine_id
        )

    if status_value is not None:
        query = query.where(
            MachineDowntime.status == status_value
        )

    return db.scalars(query).all()


def get_downtime(
    db: Session,
    downtime_id: int,
) -> MachineDowntime:
    return _get_downtime(db, downtime_id)


def update_downtime(
    db: Session,
    downtime_id: int,
    data: DowntimeUpdate,
) -> MachineDowntime:

    downtime = _get_downtime(db, downtime_id)

    if downtime.status in (
        DowntimeStatus.RESOLVED,
        DowntimeStatus.CANCELLED,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resolved or cancelled downtime cannot be updated",
        )

    update_data = data.model_dump(exclude_unset=True)

    if "started_at" in update_data:
        if downtime.ended_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change start time after downtime has ended",
            )

    for field, value in update_data.items():
        setattr(downtime, field, value)

    db.commit()
    db.refresh(downtime)

    return downtime


def update_downtime_status(
    db: Session,
    downtime_id: int,
    data: DowntimeStatusUpdate,
) -> MachineDowntime:

    downtime = _get_downtime(db, downtime_id)

    current = downtime.status
    target = data.status

    if current in (
        DowntimeStatus.RESOLVED,
        DowntimeStatus.CANCELLED,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Downtime is already in a terminal state",
        )

    allowed_transitions = {
        DowntimeStatus.OPEN: {
            DowntimeStatus.IN_PROGRESS,
            DowntimeStatus.RESOLVED,
            DowntimeStatus.CANCELLED,
        },
        DowntimeStatus.IN_PROGRESS: {
            DowntimeStatus.RESOLVED,
            DowntimeStatus.CANCELLED,
        },
    }

    if target not in allowed_transitions.get(current, set()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid downtime status transition: "
                f"{current.value} -> {target.value}"
            ),
        )

    if data.resolved_by is not None:
        _validate_user(
            db,
            data.resolved_by,
            "Resolved by",
        )

    if target == DowntimeStatus.IN_PROGRESS:
        downtime.status = target

    elif target == DowntimeStatus.RESOLVED:
        ended_at = data.ended_at or datetime.utcnow()

        downtime.duration_hours = _calculate_duration(
            downtime.started_at,
            ended_at,
        )

        downtime.ended_at = ended_at
        downtime.status = target

        if data.resolved_by is not None:
            downtime.resolved_by = data.resolved_by

        if data.corrective_action is not None:
            downtime.corrective_action = data.corrective_action

        if data.remarks is not None:
            downtime.remarks = data.remarks

    elif target == DowntimeStatus.CANCELLED:
        downtime.status = target

        if data.remarks is not None:
            downtime.remarks = data.remarks

    db.commit()
    db.refresh(downtime)

    return downtime


def delete_downtime(
    db: Session,
    downtime_id: int,
) -> None:

    downtime = _get_downtime(db, downtime_id)

    if downtime.status not in (
        DowntimeStatus.OPEN,
        DowntimeStatus.CANCELLED,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only open or cancelled downtime "
                "records can be deleted"
            ),
        )

    db.delete(downtime)
    db.commit()