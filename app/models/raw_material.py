from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class RawMaterialStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class RawMaterial(Base):
    __tablename__ = "raw_materials"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    material_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    supplier: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    available_quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    minimum_stock: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    reorder_level: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    status: Mapped[RawMaterialStatus] = mapped_column(
        SQLEnum(RawMaterialStatus),
        nullable=False,
        default=RawMaterialStatus.ACTIVE,
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