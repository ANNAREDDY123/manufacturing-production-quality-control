from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import require_roles
from app.db.database import get_db
from app.models.production_line import ProductionLineStatus
from app.models.user import User, UserRole
from app.schemas.production_line import (
    ProductionLineCreate,
    ProductionLineResponse,
    ProductionLineStatusUpdate,
    ProductionLineUpdate,
)
from app.services.production_line_service import (
    create_production_line,
    delete_production_line,
    get_production_line,
    list_production_lines,
    update_production_line,
    update_production_line_status,
)


MANAGEMENT_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
)

VIEW_ROLES = tuple(
    role
    for role in UserRole
    if role != UserRole.WORKER
)

STATUS_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
)

router = APIRouter(
    prefix="/production-lines",
    tags=["Production Lines"],
)


@router.post(
    "",
    response_model=ProductionLineResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_line(
    data: ProductionLineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        return create_production_line(
            db,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[ProductionLineResponse],
)
def get_lines(
    search: str | None = Query(
        default=None,
        min_length=1,
    ),
    status_filter: ProductionLineStatus | None = Query(
        default=None,
        alias="status",
    ),
    plant_id: int | None = Query(
        default=None,
        gt=0,
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
        require_roles(*VIEW_ROLES)
    ),
):
    return list_production_lines(
        db,
        search=search,
        status=status_filter,
        plant_id=plant_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{line_id}",
    response_model=ProductionLineResponse,
)
def get_line(
    line_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    production_line = get_production_line(
        db,
        line_id,
    )

    if production_line is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production line not found",
        )

    return production_line


@router.put(
    "/{line_id}",
    response_model=ProductionLineResponse,
)
def update_line(
    line_id: int,
    data: ProductionLineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    production_line = get_production_line(
        db,
        line_id,
    )

    if production_line is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production line not found",
        )

    try:
        return update_production_line(
            db,
            production_line,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{line_id}/status",
    response_model=ProductionLineResponse,
)
def change_line_status(
    line_id: int,
    data: ProductionLineStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*STATUS_ROLES)
    ),
):
    production_line = get_production_line(
        db,
        line_id,
    )

    if production_line is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production line not found",
        )

    return update_production_line_status(
        db,
        production_line,
        data.status,
    )


@router.delete(
    "/{line_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_line(
    line_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    production_line = get_production_line(
        db,
        line_id,
    )

    if production_line is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production line not found",
        )

    delete_production_line(
        db,
        production_line,
    )

    return None