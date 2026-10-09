from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.audit_log import (
    AuditLogCreate,
    AuditLogResponse,
)
from app.services.audit_log_service import (
    create_audit_log,
    delete_audit_log,
    get_audit_log,
    list_audit_logs,
)


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


VIEW_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.QUALITY_MANAGER,
    UserRole.MAINTENANCE_ENGINEER,
    UserRole.STORE_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
}

MANAGE_ROLES = {
    UserRole.SUPER_ADMIN,
}


def check_view_access(
    current_user: User,
) -> None:
    if current_user.role not in VIEW_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


def check_manage_access(
    current_user: User,
) -> None:
    if current_user.role not in MANAGE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


@router.post(
    "",
    response_model=AuditLogResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_audit_log_endpoint(
    data: AuditLogCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_manage_access(current_user)

    if data.user_id is None:
        data.user_id = current_user.id

    if data.username is None:
        data.username = current_user.username

    if data.ip_address is None:
        client = request.client

        if client is not None:
            data.ip_address = client.host

    if data.user_agent is None:
        data.user_agent = request.headers.get(
            "user-agent"
        )

    if data.request_method is None:
        data.request_method = request.method

    if data.request_path is None:
        data.request_path = request.url.path

    return create_audit_log(
        db,
        data,
    )


@router.get(
    "",
    response_model=list[AuditLogResponse],
)
def get_audit_logs(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    user_id: int | None = Query(
        default=None,
        gt=0,
    ),
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: int | None = Query(
        default=None,
        gt=0,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_view_access(current_user)

    return list_audit_logs(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
    )


@router.get(
    "/{audit_log_id}",
    response_model=AuditLogResponse,
)
def get_audit_log_endpoint(
    audit_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_view_access(current_user)

    try:
        return get_audit_log(
            db,
            audit_log_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{audit_log_id}",
    response_model=AuditLogResponse,
)
def delete_audit_log_endpoint(
    audit_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_manage_access(current_user)

    try:
        return delete_audit_log(
            db,
            audit_log_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc