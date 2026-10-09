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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class QualityInspectionStatus(str, Enum):
    PENDING = "Pending"
    PASSED = "Passed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class QualityInspection(Base):
    __tablename__ = "quality_inspections"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    inspection_number: Mapped[str] = mapped_column(
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

    inspector_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    inspection_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    sample_quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    accepted_quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    rejected_quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    status: Mapped[QualityInspectionStatus] = mapped_column(
        SQLEnum(QualityInspectionStatus),
        nullable=False,
        default=QualityInspectionStatus.PENDING,
        index=True,
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

    production_batch = relationship(
        "ProductionBatch",
        foreign_keys=[production_batch_id],
    )

    inspector = relationship(
        "User",
        foreign_keys=[inspector_id],
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by],
    )

    @property
    def acceptance_percentage(self) -> float:
        if self.sample_quantity <= 0:
            return 0.0

        return round(
            (self.accepted_quantity / self.sample_quantity) * 100,
            2,
        )

    @property
    def rejection_percentage(self) -> float:
        if self.sample_quantity <= 0:
            return 0.0

        return round(
            (self.rejected_quantity / self.sample_quantity) * 100,
            2,
        )