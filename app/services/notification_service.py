from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
    NotificationStatus,
)
from app.models.user import User
from app.schemas.notification import (
    NotificationCreate,
)


def _get_notification(
    db: Session,
    notification_id: int,
) -> Notification:
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id
        )
    )

    if notification is None:
        raise ValueError("Notification not found")

    return notification


def _get_user(
    db: Session,
    user_id: int,
) -> User:
    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if user is None:
        raise ValueError("User not found")

    return user


def create_notification(
    db: Session,
    data: NotificationCreate,
    created_by: int | None = None,
) -> Notification:

    _get_user(db, data.user_id)

    if created_by is not None:
        _get_user(db, created_by)

    notification = Notification(
        user_id=data.user_id,
        notification_type=data.notification_type,
        status=NotificationStatus.UNREAD,
        title=data.title,
        message=data.message,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        created_by=created_by,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


def get_notification(
    db: Session,
    notification_id: int,
) -> Notification:

    return _get_notification(
        db,
        notification_id,
    )


def list_notifications(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    status: NotificationStatus | None = None,
    notification_type=None,
) -> list[Notification]:

    query = select(Notification).where(
        Notification.user_id == user_id
    )

    if status is not None:
        query = query.where(
            Notification.status == status
        )

    if notification_type is not None:
        query = query.where(
            Notification.notification_type
            == notification_type
        )

    query = (
        query
        .order_by(Notification.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(
        db.scalars(query).all()
    )


def count_unread_notifications(
    db: Session,
    user_id: int,
) -> int:

    from sqlalchemy import func

    query = select(
        func.count(Notification.id)
    ).where(
        Notification.user_id == user_id,
        Notification.status
        == NotificationStatus.UNREAD,
    )

    return int(db.scalar(query) or 0)


def mark_notification_read(
    db: Session,
    notification_id: int,
    user_id: int,
) -> Notification:

    notification = _get_notification(
        db,
        notification_id,
    )

    if notification.user_id != user_id:
        raise PermissionError(
            "You can only modify your own notifications"
        )

    if notification.status != NotificationStatus.READ:
        notification.status = NotificationStatus.READ
        notification.read_at = datetime.utcnow()

        db.commit()
        db.refresh(notification)

    return notification


def mark_all_notifications_read(
    db: Session,
    user_id: int,
) -> int:

    notifications = list(
        db.scalars(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.status
                == NotificationStatus.UNREAD,
            )
        ).all()
    )

    now = datetime.utcnow()

    for notification in notifications:
        notification.status = NotificationStatus.READ
        notification.read_at = now

    db.commit()

    return len(notifications)


def delete_notification(
    db: Session,
    notification_id: int,
    user_id: int,
) -> Notification:

    notification = _get_notification(
        db,
        notification_id,
    )

    if notification.user_id != user_id:
        raise PermissionError(
            "You can only delete your own notifications"
        )

    db.delete(notification)
    db.commit()

    return notification