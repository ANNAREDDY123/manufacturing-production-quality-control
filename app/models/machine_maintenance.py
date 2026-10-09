from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class MaintenanceType(str, Enum):
    PREVENTIVE = "Preventive"
    CORRECTIVE = "Corrective"
    EMERGENCY = "Emergency"


class MaintenanceStatus(str, Enum):
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class MachineMaintenance(Base):
    __tablename__ = "machine_maintenance"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    maintenance_number: Mapped[str] = mapped_column(
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

    maintenance_type: Mapped[MaintenanceType] = mapped_column(
        SQLEnum(MaintenanceType),
        nullable=False,
        index=True,
    )

    status: Mapped[MaintenanceStatus] = mapped_column(
        SQLEnum(MaintenanceStatus),
        nullable=False,
        default=MaintenanceStatus.SCHEDULED,
        index=True,
    )

    scheduled_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    technician_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    findings: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    actions_taken: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    spare_parts_used: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    maintenance_cost: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    downtime_hours: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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