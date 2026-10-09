from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class PlantStatus(str, Enum):
    ACTIVE = "Active"
    MAINTENANCE = "Maintenance"
    TEMPORARILY_CLOSED = "Temporarily Closed"
    INACTIVE = "Inactive"


class Plant(Base):
    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    plant_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    address: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="India",
    )

    capacity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    status: Mapped[PlantStatus] = mapped_column(
        SQLEnum(PlantStatus),
        nullable=False,
        default=PlantStatus.ACTIVE,
    )

    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    manager = relationship(
        "User",
        foreign_keys=[manager_id],
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )