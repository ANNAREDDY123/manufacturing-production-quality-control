from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.plant import Plant, PlantStatus
from app.models.user import User, UserRole
from app.schemas.plant import PlantCreate, PlantUpdate


def validate_manager(
    db: Session,
    manager_id: int | None,
) -> None:
    if manager_id is None:
        return

    manager = db.scalar(
        select(User).where(User.id == manager_id)
    )

    if manager is None:
        raise ValueError("Manager not found")

    if not manager.is_active:
        raise ValueError("Manager account is inactive")

    if manager.role != UserRole.PLANT_MANAGER:
        raise ValueError(
            "Assigned manager must have the Plant Manager role"
        )


def create_plant(
    db: Session,
    plant_data: PlantCreate,
) -> Plant:
    existing_plant = db.scalar(
        select(Plant).where(
            Plant.plant_code == plant_data.plant_code
        )
    )

    if existing_plant:
        raise ValueError("Plant code already exists")

    validate_manager(
        db,
        plant_data.manager_id,
    )

    plant = Plant(
        plant_code=plant_data.plant_code,
        name=plant_data.name,
        description=plant_data.description,
        address=plant_data.address,
        city=plant_data.city,
        state=plant_data.state,
        country=plant_data.country,
        capacity=plant_data.capacity,
        status=plant_data.status,
        manager_id=plant_data.manager_id,
    )

    db.add(plant)
    db.commit()
    db.refresh(plant)

    return plant


def get_plant(
    db: Session,
    plant_id: int,
) -> Plant | None:
    return db.scalar(
        select(Plant).where(Plant.id == plant_id)
    )


def list_plants(
    db: Session,
    search: str | None = None,
    status: PlantStatus | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Plant]:
    query = select(Plant)

    if search:
        search_value = f"%{search}%"

        query = query.where(
            or_(
                Plant.plant_code.ilike(search_value),
                Plant.name.ilike(search_value),
                Plant.city.ilike(search_value),
                Plant.state.ilike(search_value),
            )
        )

    if status:
        query = query.where(
            Plant.status == status
        )

    query = query.order_by(
        Plant.id.desc()
    )

    query = query.offset(skip).limit(limit)

    return list(db.scalars(query).all())


def update_plant(
    db: Session,
    plant: Plant,
    plant_data: PlantUpdate,
) -> Plant:
    if plant_data.manager_id is not None:
        validate_manager(
            db,
            plant_data.manager_id,
        )

    update_data = plant_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(plant, field, value)

    db.commit()
    db.refresh(plant)

    return plant


def update_plant_status(
    db: Session,
    plant: Plant,
    status: PlantStatus,
) -> Plant:
    plant.status = status

    db.commit()
    db.refresh(plant)

    return plant