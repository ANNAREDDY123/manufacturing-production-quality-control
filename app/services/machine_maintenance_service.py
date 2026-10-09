from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.machine import Machine
from app.models.machine_maintenance import (
    MachineMaintenance,
    MaintenanceStatus,
)
from app.models.user import User
from app.schemas.machine_maintenance import (
    MachineMaintenanceCreate,
    MachineMaintenanceStatusUpdate,
    MachineMaintenanceUpdate,
)


def _get_maintenance(
    db: Session,
    maintenance_id: int,
) -> MachineMaintenance:
    maintenance = db.scalar(
        select(MachineMaintenance).where(
            MachineMaintenance.id == maintenance_id
        )
    )

    if maintenance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine maintenance record not found",
        )

    return maintenance


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
            detail=f"{field_name} not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} account is inactive",
        )

    return user


def create_maintenance(
    db: Session,
    data: MachineMaintenanceCreate,
    created_by: int,
) -> MachineMaintenance:

    existing = db.scalar(
        select(MachineMaintenance).where(
            MachineMaintenance.maintenance_number
            == data.maintenance_number
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Maintenance number already exists",
        )

    _validate_machine(
        db,
        data.machine_id,
    )

    if data.technician_id is not None:
        _validate_user(
            db,
            data.technician_id,
            "Technician",
        )

    maintenance = MachineMaintenance(
        maintenance_number=data.maintenance_number,
        machine_id=data.machine_id,
        maintenance_type=data.maintenance_type,
        status=MaintenanceStatus.SCHEDULED,
        scheduled_date=data.scheduled_date,
        technician_id=data.technician_id,
        description=data.description,
        findings=data.findings,
        actions_taken=data.actions_taken,
        spare_parts_used=data.spare_parts_used,
        maintenance_cost=data.maintenance_cost,
        downtime_hours=data.downtime_hours,
        remarks=data.remarks,
        created_by=created_by,
    )

    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)

    return maintenance


def get_maintenance(
    db: Session,
    maintenance_id: int,
) -> MachineMaintenance:
    return _get_maintenance(
        db,
        maintenance_id,
    )


def list_maintenance(
    db: Session,
    machine_id: int | None = None,
    maintenance_status: MaintenanceStatus | None = None,
) -> list[MachineMaintenance]:

    query = select(MachineMaintenance)

    if machine_id is not None:
        query = query.where(
            MachineMaintenance.machine_id == machine_id
        )

    if maintenance_status is not None:
        query = query.where(
            MachineMaintenance.status
            == maintenance_status
        )

    query = query.order_by(
        MachineMaintenance.id.desc()
    )

    return list(db.scalars(query).all())


def update_maintenance(
    db: Session,
    maintenance_id: int,
    data: MachineMaintenanceUpdate,
) -> MachineMaintenance:

    maintenance = _get_maintenance(
        db,
        maintenance_id,
    )

    if maintenance.status in (
        MaintenanceStatus.COMPLETED,
        MaintenanceStatus.CANCELLED,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completed or cancelled maintenance cannot be updated",
        )

    values = data.model_dump(
        exclude_unset=True
    )

    if "technician_id" in values:
        technician_id = values["technician_id"]

        if technician_id is not None:
            _validate_user(
                db,
                technician_id,
                "Technician",
            )

    for field, value in values.items():
        setattr(
            maintenance,
            field,
            value,
        )

    db.commit()
    db.refresh(maintenance)

    return maintenance


def update_maintenance_status(
    db: Session,
    maintenance_id: int,
    data: MachineMaintenanceStatusUpdate,
) -> MachineMaintenance:

    maintenance = _get_maintenance(
        db,
        maintenance_id,
    )

    current_status = maintenance.status
    new_status = data.status

    if current_status == MaintenanceStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cancelled maintenance is terminal",
        )

    if current_status == MaintenanceStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completed maintenance is terminal",
        )

    allowed_transitions = {
        MaintenanceStatus.SCHEDULED: {
            MaintenanceStatus.IN_PROGRESS,
            MaintenanceStatus.CANCELLED,
        },
        MaintenanceStatus.IN_PROGRESS: {
            MaintenanceStatus.COMPLETED,
            MaintenanceStatus.CANCELLED,
        },
    }

    if new_status not in allowed_transitions.get(
        current_status,
        set(),
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot transition maintenance from "
                f"{current_status.value} to {new_status.value}"
            ),
        )

    if new_status == MaintenanceStatus.IN_PROGRESS:
        maintenance.started_at = datetime.utcnow()

    if new_status == MaintenanceStatus.COMPLETED:
        if maintenance.started_at is None:
            maintenance.started_at = datetime.utcnow()

        maintenance.completed_at = datetime.utcnow()

    maintenance.status = new_status

    db.commit()
    db.refresh(maintenance)

    return maintenance


def delete_maintenance(
    db: Session,
    maintenance_id: int,
) -> None:

    maintenance = _get_maintenance(
        db,
        maintenance_id,
    )

    if maintenance.status not in (
        MaintenanceStatus.SCHEDULED,
        MaintenanceStatus.CANCELLED,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only scheduled or cancelled maintenance can be deleted",
        )

    db.delete(maintenance)
    db.commit()