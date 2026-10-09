from datetime import date, datetime, time
from enum import Enum

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ShiftType(str, Enum):
    MORNING = "Morning"
    EVENING = "Evening"
    NIGHT = "Night"


class ShiftStatus(str, Enum):
    PLANNED = "Planned"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    shift_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    shift_type: Mapped[ShiftType] = mapped_column(
        SQLEnum(ShiftType),
        nullable=False,
        index=True,
    )

    shift_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    scheduled_start: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    scheduled_end: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    actual_start: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    actual_end: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    production_line_id: Mapped[int | None] = mapped_column(
        ForeignKey("production_lines.id"),
        nullable=True,
        index=True,
    )

    supervisor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    planned_output: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    production_output: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    rejected_output: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    machine_usage_hours: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    performance_percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    status: Mapped[ShiftStatus] = mapped_column(
        SQLEnum(ShiftStatus),
        nullable=False,
        default=ShiftStatus.PLANNED,
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

    supervisor = relationship(
        "User",
        foreign_keys=[supervisor_id],
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by],
    )

    worker_assignments = relationship(
        "ShiftWorker",
        back_populates="shift",
        cascade="all, delete-orphan",
    )

    @property
    def completion_percentage(self) -> float:
        if self.planned_output <= 0:
            return 0.0

        return round(
            min((self.production_output / self.planned_output) * 100, 100),
            2,
        )

    @property
    def rejection_percentage(self) -> float:
        total = self.production_output + self.rejected_output

        if total <= 0:
            return 0.0

        return round(
            (self.rejected_output / total) * 100,
            2,
        )