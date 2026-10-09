from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.notification import (
    NotificationStatus,
    NotificationType,
)


class NotificationCreate(BaseModel):
    user_id: int = Field(gt=0)

    notification_type: NotificationType

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    message: str = Field(
        min_length=1,
    )

    entity_type: str | None = Field(
        default=None,
        max_length=100,
    )

    entity_id: int | None = Field(
        default=None,
        gt=0,
    )


class NotificationStatusUpdate(BaseModel):
    status: NotificationStatus


class NotificationResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    user_id: int
    notification_type: NotificationType
    status: NotificationStatus
    title: str
    message: str
    entity_type: str | None
    entity_id: int | None
    created_by: int | None
    read_at: datetime | None
    created_at: datetime