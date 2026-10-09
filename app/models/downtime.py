from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class DowntimeReason(str, Enum):
    MACHINE_BREAKDOWN = "Machine Breakdown"
    MAINTENANCE = "Maintenance"
    MATERIAL_SHORTAGE = "Material Shortage"
    POWER_FAILURE = "Power Failure"
    OPERATOR_UNAVAILABLE = "Operator Unavailable"
    QUALITY_ISSUE = "Quality Issue"
    SETUP_CHANGEOVER = "Setup Changeover"
    PLANNED_STOPPAGE = "Planned Stoppage"
    OTHER = "Other"


class DowntimeStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CANCELLED = "Cancelled"


class MachineDowntime(Base):
    __tablename__ = "machine_downtime"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    downtime_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machines.id"),
        nullable=False,
        index=True,
    )

    reason: Mapped[DowntimeReason] = mapped_column(
        SQLEnum(DowntimeReason),
        nullable=False,
        index=True,
    )

    status: Mapped[DowntimeStatus] = mapped_column(
        SQLEnum(DowntimeStatus),
        nullable=False,
        default=DowntimeStatus.OPEN,
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    duration_hours: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    reported_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    resolved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    root_cause: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    corrective_action: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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