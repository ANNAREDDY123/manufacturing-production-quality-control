from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import require_roles
from app.db.database import get_db
from app.models.bom import BOMStatus
from app.models.user import User, UserRole
from app.schemas.bom import (
    BOMCreate,
    BOMItemCreate,
    BOMItemResponse,
    BOMItemUpdate,
    BOMResponse,
    BOMStatusUpdate,
    BOMUpdate,
)
from app.services.bom_service import (
    add_bom_item,
    create_bom,
    get_bom,
    list_boms,
    remove_bom_item,
    update_bom,
    update_bom_item,
    update_bom_status,
)


router = APIRouter(
    prefix="/boms",
    tags=["BOM"],
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


@router.post(
    "/products/{product_id}",
    response_model=BOMResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product_bom(
    product_id: int,
    data: BOMCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        return create_bom(
            db,
            product_id,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/products/{product_id}",
    response_model=list[BOMResponse],
)
def get_product_boms(
    product_id: int,
    status_filter: BOMStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    try:
        return list_boms(
            db,
            product_id,
            status_filter,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{bom_id}",
    response_model=BOMResponse,
)
def get_bom_details(
    bom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    try:
        return get_bom(
            db,
            bom_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.put(
    "/{bom_id}",
    response_model=BOMResponse,
)
def update_bom_details(
    bom_id: int,
    data: BOMUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        return update_bom(
            db,
            bom_id,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{bom_id}/items",
    response_model=BOMItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_item(
    bom_id: int,
    data: BOMItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        return add_bom_item(
            db,
            bom_id,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.put(
    "/{bom_id}/items/{item_id}",
    response_model=BOMItemResponse,
)
def update_item(
    bom_id: int,
    item_id: int,
    data: BOMItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        return update_bom_item(
            db,
            bom_id,
            item_id,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{bom_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_item(
    bom_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        remove_bom_item(
            db,
            bom_id,
            item_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{bom_id}/status",
    response_model=BOMResponse,
)
def change_bom_status(
    bom_id: int,
    data: BOMStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
):
    try:
        return update_bom_status(
            db,
            bom_id,
            data.status,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc