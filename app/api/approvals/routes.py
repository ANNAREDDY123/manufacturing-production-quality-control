from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import require_roles
from app.db.database import get_db
from app.models.production_approval import (
    ProductionApprovalStatus,
)
from app.models.user import UserRole
from app.schemas.production_approval import (
    ProductionApprovalCreate,
    ProductionApprovalResponse,
    ProductionApprovalStatusUpdate,
    ProductionApprovalUpdate,
)
from app.services.production_approval_service import (
    create_production_approval,
    delete_production_approval,
    get_production_approval,
    list_production_approvals,
    update_production_approval,
    update_production_approval_status,
)


router = APIRouter(
    prefix="/production-approvals",
    tags=["Production Approvals"],
)


# Users who can request/manage an approval.
REQUEST_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.PRODUCTION_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
)


# Users who can approve/reject.
APPROVER_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
)


# Users who can view approval records.
VIEW_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
    UserRole.QUALITY_MANAGER,
)


@router.post(
    "",
    response_model=ProductionApprovalResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: ProductionApprovalCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*REQUEST_ROLES)
    ),
):
    # The authenticated requester is authoritative.
    data.requested_by = current_user.id

    return create_production_approval(
        db,
        data,
    )


@router.get(
    "",
    response_model=list[ProductionApprovalResponse],
)
def list_all(
    production_batch_id: int | None = Query(
        default=None,
        gt=0,
    ),
    production_order_id: int | None = Query(
        default=None,
        gt=0,
    ),
    approval_status: ProductionApprovalStatus | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    return list_production_approvals(
        db,
        production_batch_id=production_batch_id,
        production_order_id=production_order_id,
        approval_status=approval_status,
    )


@router.get(
    "/{approval_id}",
    response_model=ProductionApprovalResponse,
)
def get_one(
    approval_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*VIEW_ROLES)
    ),
):
    return get_production_approval(
        db,
        approval_id,
    )


@router.put(
    "/{approval_id}",
    response_model=ProductionApprovalResponse,
)
def update(
    approval_id: int,
    data: ProductionApprovalUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*REQUEST_ROLES)
    ),
):
    return update_production_approval(
        db,
        approval_id,
        data,
    )


@router.patch(
    "/{approval_id}/status",
    response_model=ProductionApprovalResponse,
)
def update_status(
    approval_id: int,
    data: ProductionApprovalStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*APPROVER_ROLES)
    ),
):
    # Do not allow a caller to approve as another user.
    if data.status in {
        ProductionApprovalStatus.APPROVED,
        ProductionApprovalStatus.REJECTED,
    }:
        data.approver_id = current_user.id

    return update_production_approval_status(
        db,
        approval_id,
        data,
    )


@router.delete(
    "/{approval_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    approval_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(*REQUEST_ROLES)
    ),
):
    delete_production_approval(
        db,
        approval_id,
    )