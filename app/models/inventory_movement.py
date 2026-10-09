from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class InventoryMovementType(str, Enum):
    STOCK_IN = "Stock In"
    STOCK_OUT = "Stock Out"
    ADJUSTMENT = "Adjustment"

    # Backward-compatible name used by some Level 16 code/tests.
    STOCK_ADJUSTMENT = "Adjustment"


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    material_id: Mapped[int] = mapped_column(
        ForeignKey("raw_materials.id"),
        nullable=False,
        index=True,
    )

    movement_type: Mapped[InventoryMovementType] = mapped_column(
        SQLEnum(InventoryMovementType),
        nullable=False,
        index=True,
    )

    quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    previous_quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    new_quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        String(500),
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