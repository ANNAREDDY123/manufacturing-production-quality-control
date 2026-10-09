from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class MachineStatus(str, Enum):
    RUNNING = "Running"
    IDLE = "Idle"
    MAINTENANCE = "Maintenance"
    BREAKDOWN = "Breakdown"
    DECOMMISSIONED = "Decommissioned"


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    machine_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    machine_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    production_line_id: Mapped[int] = mapped_column(
        ForeignKey("production_lines.id"),
        nullable=False,
        index=True,
    )

    installation_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[MachineStatus] = mapped_column(
        SQLEnum(MachineStatus),
        nullable=False,
        default=MachineStatus.IDLE,
        index=True,
    )

    operating_hours: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
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