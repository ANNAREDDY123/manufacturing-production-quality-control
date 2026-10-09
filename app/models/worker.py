from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class WorkerStatus(str, Enum):
    ACTIVE = "Active"
    ON_LEAVE = "On Leave"
    INACTIVE = "Inactive"


class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    employee_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    skill: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    department: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    shift: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    production_line_id: Mapped[int | None] = mapped_column(
        ForeignKey("production_lines.id"),
        nullable=True,
        index=True,
    )

    status: Mapped[WorkerStatus] = mapped_column(
        SQLEnum(WorkerStatus),
        nullable=False,
        default=WorkerStatus.ACTIVE,
        index=True,
    )

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
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

    production_line = relationship(
        "ProductionLine",
        foreign_keys=[production_line_id],
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by],
    )