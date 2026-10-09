from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditLogCreate(BaseModel):
    user_id: int | None = Field(
        default=None,
        gt=0,
    )

    username: str | None = Field(
        default=None,
        max_length=100,
    )

    action: str = Field(
        min_length=1,
        max_length=50,
    )

    entity_type: str = Field(
        min_length=1,
        max_length=100,
    )

    entity_id: int | None = Field(
        default=None,
        gt=0,
    )

    description: str | None = None

    old_values: str | None = None

    new_values: str | None = None

    ip_address: str | None = Field(
        default=None,
        max_length=45,
    )

    user_agent: str | None = Field(
        default=None,
        max_length=500,
    )

    request_method: str | None = Field(
        default=None,
        max_length=10,
    )

    request_path: str | None = Field(
        default=None,
        max_length=500,
    )


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    user_id: int | None
    username: str | None
    action: str
    entity_type: str
    entity_id: int | None
    description: str | None
    old_values: str | None
    new_values: str | None
    ip_address: str | None
    user_agent: str | None
    request_method: str | None
    request_path: str | None
    created_at: datetime