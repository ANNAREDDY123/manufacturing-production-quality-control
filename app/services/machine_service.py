from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.machine import Machine, MachineStatus
from app.models.production_line import ProductionLine
from app.schemas.machine import (
    MachineCreate,
    MachineStatusUpdate,
    MachineUpdate,
)


MANAGEABLE_STATUSES = {
    MachineStatus.RUNNING,
    MachineStatus.IDLE,
    MachineStatus.MAINTENANCE,
    MachineStatus.BREAKDOWN,
    MachineStatus.DECOMMISSIONED,
}


def _get_machine(
    db: Session,
    machine_id: int,
) -> Machine:
    machine = db.scalar(
        select(Machine).where(
            Machine.id == machine_id
        )
    )

    if machine is None:
        raise ValueError("Machine not found")

    return machine


def _get_production_line(
    db: Session,
    production_line_id: int,
) -> ProductionLine:
    line = db.scalar(
        select(ProductionLine).where(
            ProductionLine.id == production_line_id
        )
    )

    if line is None:
        raise ValueError("Production line not found")

    return line


def create_machine(
    db: Session,
    data: MachineCreate,
) -> Machine:
    existing = db.scalar(
        select(Machine).where(
            Machine.machine_code == data.machine_code
        )
    )

    if existing:
        raise ValueError(
            "Machine code already registered"
        )

    if data.installation_date > date.today():
        raise ValueError(
            "Installation date cannot be in the future"
        )

    _get_production_line(
        db,
        data.production_line_id,
    )

    machine = Machine(
        machine_code=data.machine_code,
        name=data.name,
        machine_type=data.machine_type,
        production_line_id=data.production_line_id,
        installation_date=data.installation_date,
        status=data.status,
        operating_hours=data.operating_hours,
    )

    db.add(machine)
    db.commit()
    db.refresh(machine)

    return machine


def get_machine(
    db: Session,
    machine_id: int,
) -> Machine:
    return _get_machine(
        db,
        machine_id,
    )


def list_machines(
    db: Session,
    search: str | None = None,
    machine_type: str | None = None,
    production_line_id: int | None = None,
    status: MachineStatus | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Machine]:
    query = select(Machine)

    if search:
        search_value = f"%{search}%"

        query = query.where(
            or_(
                Machine.machine_code.ilike(search_value),
                Machine.name.ilike(search_value),
            )
        )

    if machine_type:
        query = query.where(
            Machine.machine_type == machine_type
        )

    if production_line_id is not None:
        query = query.where(
            Machine.production_line_id
            == production_line_id
        )

    if status is not None:
        query = query.where(
            Machine.status == status
        )

    query = (
        query
        .order_by(Machine.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(
        db.scalars(query).all()
    )


def update_machine(
    db: Session,
    machine_id: int,
    data: MachineUpdate,
) -> Machine:
    machine = _get_machine(
        db,
        machine_id,
    )

    if machine.status == MachineStatus.DECOMMISSIONED:
        raise ValueError(
            "Decommissioned machine cannot be modified"
        )

    if (
        data.installation_date is not None
        and data.installation_date > date.today()
    ):
        raise ValueError(
            "Installation date cannot be in the future"
        )

    if data.production_line_id is not None:
        _get_production_line(
            db,
            data.production_line_id,
        )
        machine.production_line_id = (
            data.production_line_id
        )

    if data.name is not None:
        machine.name = data.name

    if data.machine_type is not None:
        machine.machine_type = data.machine_type

    if data.installation_date is not None:
        machine.installation_date = (
            data.installation_date
        )

    if data.operating_hours is not None:
        machine.operating_hours = (
            data.operating_hours
        )

    db.commit()
    db.refresh(machine)

    return machine


def update_machine_status(
    db: Session,
    machine_id: int,
    data: MachineStatusUpdate,
) -> Machine:
    machine = _get_machine(
        db,
        machine_id,
    )

    if (
        machine.status == MachineStatus.DECOMMISSIONED
        and data.status != MachineStatus.DECOMMISSIONED
    ):
        raise ValueError(
            "Decommissioned machine cannot be reactivated"
        )

    machine.status = data.status

    db.commit()
    db.refresh(machine)

    return machine


def delete_machine(
    db: Session,
    machine_id: int,
) -> None:
    machine = _get_machine(
        db,
        machine_id,
    )

    if machine.status != MachineStatus.DECOMMISSIONED:
        raise ValueError(
            "Only decommissioned machines can be deleted"
        )

    db.delete(machine)
    db.commit()