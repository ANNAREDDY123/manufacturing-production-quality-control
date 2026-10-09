from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.plant import Plant
from app.models.production_line import (
    ProductionLine,
    ProductionLineStatus,
)
from app.models.user import User, UserRole
from app.schemas.production_line import (
    ProductionLineCreate,
    ProductionLineUpdate,
)


def validate_plant(
    db: Session,
    plant_id: int,
) -> None:
    plant = db.scalar(
        select(Plant).where(Plant.id == plant_id)
    )

    if plant is None:
        raise ValueError("Plant not found")

    if plant.status.value == "Inactive":
        raise ValueError("Cannot assign production line to an inactive plant")


def validate_supervisor(
    db: Session,
    supervisor_id: int | None,
) -> None:
    if supervisor_id is None:
        return

    supervisor = db.scalar(
        select(User).where(User.id == supervisor_id)
    )

    if supervisor is None:
        raise ValueError("Supervisor not found")

    if not supervisor.is_active:
        raise ValueError("Supervisor account is inactive")

    if supervisor.role != UserRole.PRODUCTION_SUPERVISOR:
        raise ValueError(
            "Assigned supervisor must have the Production Supervisor role"
        )


def create_production_line(
    db: Session,
    line_data: ProductionLineCreate,
) -> ProductionLine:
    existing_line = db.scalar(
        select(ProductionLine).where(
            ProductionLine.line_code == line_data.line_code
        )
    )

    if existing_line:
        raise ValueError("Production line code already exists")

    validate_plant(db, line_data.plant_id)
    validate_supervisor(db, line_data.supervisor_id)

    production_line = ProductionLine(
        line_code=line_data.line_code,
        name=line_data.name,
        capacity=line_data.capacity,
        plant_id=line_data.plant_id,
        supervisor_id=line_data.supervisor_id,
        status=line_data.status,
    )

    db.add(production_line)
    db.commit()
    db.refresh(production_line)

    return production_line


def get_production_line(
    db: Session,
    line_id: int,
) -> ProductionLine | None:
    return db.scalar(
        select(ProductionLine).where(
            ProductionLine.id == line_id
        )
    )


def list_production_lines(
    db: Session,
    search: str | None = None,
    status: ProductionLineStatus | None = None,
    plant_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[ProductionLine]:

    query = select(ProductionLine)

    if search:
        search_value = f"%{search}%"

        query = query.where(
            or_(
                ProductionLine.line_code.ilike(search_value),
                ProductionLine.name.ilike(search_value),
            )
        )

    if status:
        query = query.where(
            ProductionLine.status == status
        )

    if plant_id:
        query = query.where(
            ProductionLine.plant_id == plant_id
        )

    query = (
        query
        .order_by(ProductionLine.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(query).all())


def update_production_line(
    db: Session,
    production_line: ProductionLine,
    line_data: ProductionLineUpdate,
) -> ProductionLine:

    update_data = line_data.model_dump(
        exclude_unset=True
    )

    if "plant_id" in update_data:
        validate_plant(
            db,
            update_data["plant_id"],
        )

    if "supervisor_id" in update_data:
        validate_supervisor(
            db,
            update_data["supervisor_id"],
        )

    for field, value in update_data.items():
        setattr(
            production_line,
            field,
            value,
        )

    db.commit()
    db.refresh(production_line)

    return production_line


def update_production_line_status(
    db: Session,
    production_line: ProductionLine,
    status: ProductionLineStatus,
) -> ProductionLine:

    production_line.status = status

    db.commit()
    db.refresh(production_line)

    return production_line


def delete_production_line(
    db: Session,
    production_line: ProductionLine,
) -> None:

    db.delete(production_line)
    db.commit()