from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import (
    get_current_user,
    require_roles,
)
from app.db.database import get_db
from app.models.quality_inspection import QualityInspectionStatus
from app.models.user import User, UserRole
from app.schemas.quality_inspection import (
    QualityInspectionCreate,
    QualityInspectionResponse,
    QualityInspectionStatusUpdate,
    QualityInspectionUpdate,
)
from app.services.quality_inspection_service import (
    create_inspection,
    delete_inspection,
    get_inspection,
    list_inspections,
    update_inspection,
    update_inspection_status,
)


router = APIRouter(
    prefix="/quality-inspections",
    tags=["Quality Inspection"],
)


MANAGE_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.QUALITY_MANAGER,
    UserRole.PRODUCTION_MANAGER,
)

VIEW_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.QUALITY_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
)


@router.post(
    "",
    response_model=QualityInspectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quality_inspection(
    data: QualityInspectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    return create_inspection(
        db,
        data,
        current_user.id,
    )


@router.get(
    "",
    response_model=list[QualityInspectionResponse],
)
def get_quality_inspections(
    production_batch_id: int | None = Query(
        default=None,
        gt=0,
    ),
    inspector_id: int | None = Query(
        default=None,
        gt=0,
    ),
    inspection_status: QualityInspectionStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    return list_inspections(
        db,
        production_batch_id=production_batch_id,
        inspector_id=inspector_id,
        inspection_status=inspection_status,
    )


@router.get(
    "/{inspection_id}",
    response_model=QualityInspectionResponse,
)
def get_quality_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    return get_inspection(
        db,
        inspection_id,
    )


@router.put(
    "/{inspection_id}",
    response_model=QualityInspectionResponse,
)
def update_quality_inspection(
    inspection_id: int,
    data: QualityInspectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    return update_inspection(
        db,
        inspection_id,
        data,
    )


@router.patch(
    "/{inspection_id}/status",
    response_model=QualityInspectionResponse,
)
def update_quality_inspection_status(
    inspection_id: int,
    data: QualityInspectionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    return update_inspection_status(
        db,
        inspection_id,
        data,
    )


@router.delete(
    "/{inspection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_quality_inspection(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    delete_inspection(
        db,
        inspection_id,
    )