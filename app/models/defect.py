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


class DefectSeverity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class DefectType(str, Enum):
    MATERIAL = "Material"
    DIMENSIONAL = "Dimensional"
    SURFACE = "Surface"
    FUNCTIONAL = "Functional"
    ASSEMBLY = "Assembly"
    PROCESS = "Process"
    MACHINE = "Machine"
    OTHER = "Other"


class DefectStatus(str, Enum):
    OPEN = "Open"
    UNDER_REVIEW = "Under Review"
    CORRECTIVE_ACTION = "Corrective Action"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    REJECTED = "Rejected"


class Defect(Base):
    __tablename__ = "defects"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    defect_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    production_batch_id: Mapped[int] = mapped_column(
        ForeignKey("production_batches.id"),
        nullable=False,
        index=True,
    )

    quality_inspection_id: Mapped[int | None] = mapped_column(
        ForeignKey("quality_inspections.id"),
        nullable=True,
        index=True,
    )

    reported_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    defect_type: Mapped[DefectType] = mapped_column(
        SQLEnum(DefectType),
        nullable=False,
        index=True,
    )

    severity: Mapped[DefectSeverity] = mapped_column(
        SQLEnum(DefectSeverity),
        nullable=False,
        default=DefectSeverity.MEDIUM,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    defect_quantity: Mapped[float] = mapped_column(
        Float,
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

    preventive_action: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[DefectStatus] = mapped_column(
        SQLEnum(DefectStatus),
        nullable=False,
        default=DefectStatus.OPEN,
        index=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    resolved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
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