from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ProductionOrderStatus(str, Enum):
    DRAFT = "Draft"
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class ProductionOrderPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class ProductionOrder(Base):
    __tablename__ = "production_orders"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    target_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    production_line_id: Mapped[int] = mapped_column(
        ForeignKey("production_lines.id"),
        nullable=False,
        index=True,
    )

    priority: Mapped[ProductionOrderPriority] = mapped_column(
        SQLEnum(ProductionOrderPriority),
        nullable=False,
        default=ProductionOrderPriority.MEDIUM,
        index=True,
    )

    supervisor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    status: Mapped[ProductionOrderStatus] = mapped_column(
        SQLEnum(ProductionOrderStatus),
        nullable=False,
        default=ProductionOrderStatus.DRAFT,
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

    product = relationship(
        "Product",
        foreign_keys=[product_id],
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