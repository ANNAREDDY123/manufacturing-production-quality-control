from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import require_roles
from app.db.database import get_db
from app.models.defect import (
    DefectSeverity,
    DefectStatus,
    DefectType,
)
from app.models.user import User, UserRole
from app.schemas.defect import (
    DefectCreate,
    DefectResponse,
    DefectStatusUpdate,
    DefectUpdate,
)
from app.services.defect_service import (
    create_defect,
    delete_defect,
    get_defect,
    list_defects,
    update_defect,
    update_defect_status,
)


router = APIRouter(
    prefix="/defects",
    tags=["Defects"],
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
    response_model=DefectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_defect_endpoint(
    data: DefectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    return create_defect(
        db,
        data,
        current_user.id,
    )


@router.get(
    "",
    response_model=list[DefectResponse],
)
def get_defects(
    production_batch_id: int | None = Query(
        default=None,
        gt=0,
    ),
    quality_inspection_id: int | None = Query(
        default=None,
        gt=0,
    ),
    severity: DefectSeverity | None = None,
    defect_status: DefectStatus | None = None,
    defect_type: DefectType | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    return list_defects(
        db,
        production_batch_id=production_batch_id,
        quality_inspection_id=quality_inspection_id,
        severity=severity,
        defect_status=defect_status,
        defect_type=defect_type,
    )


@router.get(
    "/{defect_id}",
    response_model=DefectResponse,
)
def get_defect_endpoint(
    defect_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    return get_defect(
        db,
        defect_id,
    )


@router.put(
    "/{defect_id}",
    response_model=DefectResponse,
)
def update_defect_endpoint(
    defect_id: int,
    data: DefectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    return update_defect(
        db,
        defect_id,
        data,
    )


@router.patch(
    "/{defect_id}/status",
    response_model=DefectResponse,
)
def update_defect_status_endpoint(
    defect_id: int,
    data: DefectStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    return update_defect_status(
        db,
        defect_id,
        data,
        current_user.id,
    )


@router.delete(
    "/{defect_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_defect_endpoint(
    defect_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    delete_defect(
        db,
        defect_id,
    )