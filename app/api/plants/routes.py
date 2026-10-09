from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import require_roles
from app.db.database import get_db
from app.models.plant import Plant, PlantStatus
from app.models.user import User, UserRole
from app.schemas.plant import (
    PlantCreate,
    PlantResponse,
    PlantStatusUpdate,
    PlantUpdate,
)
from app.services.plant_service import (
    create_plant,
    get_plant,
    list_plants,
    update_plant,
    update_plant_status,
)


router = APIRouter(
    prefix="/plants",
    tags=["Manufacturing Plants"],
)


plant_manager_roles = require_roles(
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
)


@router.post(
    "",
    response_model=PlantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_manufacturing_plant(
    plant_data: PlantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(plant_manager_roles),
):
    try:
        return create_plant(
            db,
            plant_data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[PlantResponse],
)
def get_manufacturing_plants(
    search: str | None = Query(
        default=None,
        min_length=1,
    ),
    status_filter: PlantStatus | None = Query(
        default=None,
        alias="status",
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PLANT_MANAGER,
            UserRole.PRODUCTION_MANAGER,
            UserRole.QUALITY_MANAGER,
            UserRole.MAINTENANCE_ENGINEER,
            UserRole.STORE_MANAGER,
            UserRole.PRODUCTION_SUPERVISOR,
        )
    ),
):
    return list_plants(
        db,
        search=search,
        status=status_filter,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{plant_id}",
    response_model=PlantResponse,
)
def get_manufacturing_plant(
    plant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.PLANT_MANAGER,
            UserRole.PRODUCTION_MANAGER,
            UserRole.QUALITY_MANAGER,
            UserRole.MAINTENANCE_ENGINEER,
            UserRole.STORE_MANAGER,
            UserRole.PRODUCTION_SUPERVISOR,
        )
    ),
):
    plant = get_plant(
        db,
        plant_id,
    )

    if plant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found",
        )

    return plant


@router.put(
    "/{plant_id}",
    response_model=PlantResponse,
)
def update_manufacturing_plant(
    plant_id: int,
    plant_data: PlantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(plant_manager_roles),
):
    plant = get_plant(
        db,
        plant_id,
    )

    if plant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found",
        )

    try:
        return update_plant(
            db,
            plant,
            plant_data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{plant_id}/status",
    response_model=PlantResponse,
)
def update_manufacturing_plant_status(
    plant_id: int,
    status_data: PlantStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(plant_manager_roles),
):
    plant = get_plant(
        db,
        plant_id,
    )

    if plant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found",
        )

    return update_plant_status(
        db,
        plant,
        status_data.status,
    )