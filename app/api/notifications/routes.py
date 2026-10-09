from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.api.auth.dependencies import get_current_user
from app.db.database import get_db
from app.models.notification import (
    NotificationStatus,
    NotificationType,
)
from app.models.user import User, UserRole
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
)
from app.services.notification_service import (
    count_unread_notifications,
    create_notification,
    delete_notification,
    get_notification,
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


CREATE_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.QUALITY_MANAGER,
    UserRole.MAINTENANCE_ENGINEER,
    UserRole.STORE_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
}


def check_create_access(
    current_user: User,
) -> None:

    if current_user.role not in CREATE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


def check_notification_owner(
    notification_user_id: int,
    current_user: User,
) -> None:

    if notification_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own notifications",
        )


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_notification_endpoint(
    data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    check_create_access(current_user)

    try:
        return create_notification(
            db=db,
            data=data,
            created_by=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[NotificationResponse],
)
def get_notifications(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    notification_status: NotificationStatus | None = Query(
        default=None,
        alias="status",
    ),
    notification_type: NotificationType | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return list_notifications(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status=notification_status,
        notification_type=notification_type,
    )


@router.get(
    "/unread-count",
)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return {
        "user_id": current_user.id,
        "unread_count": count_unread_notifications(
            db=db,
            user_id=current_user.id,
        ),
    }


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
)
def get_notification_endpoint(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        notification = get_notification(
            db,
            notification_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    check_notification_owner(
        notification.user_id,
        current_user,
    )

    return notification


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_notification_read_endpoint(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        return mark_notification_read(
            db=db,
            notification_id=notification_id,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.patch(
    "/read-all",
)
def mark_all_notifications_read_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    count = mark_all_notifications_read(
        db=db,
        user_id=current_user.id,
    )

    return {
        "user_id": current_user.id,
        "marked_read": count,
    }


@router.delete(
    "/{notification_id}",
    response_model=NotificationResponse,
)
def delete_notification_endpoint(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        return delete_notification(
            db=db,
            notification_id=notification_id,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc