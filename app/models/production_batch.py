from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ProductionBatchStatus(str, Enum):
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class ProductionBatch(Base):
    __tablename__ = "production_batches"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    batch_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    production_order_id: Mapped[int] = mapped_column(
        ForeignKey("production_orders.id"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    supervisor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    status: Mapped[ProductionBatchStatus] = mapped_column(
        SQLEnum(ProductionBatchStatus),
        nullable=False,
        default=ProductionBatchStatus.PLANNED,
        index=True,
    )

    planned_start: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    actual_start: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    actual_end: Mapped[datetime | None] = mapped_column(
        DateTime,
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

    production_order = relationship(
        "ProductionOrder",
        foreign_keys=[production_order_id],
    )

    supervisor = relationship(
        "User",
        foreign_keys=[supervisor_id],
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by],
    )