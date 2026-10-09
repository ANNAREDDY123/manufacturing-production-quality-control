from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class BOMStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class BOM(Base):
    __tablename__ = "boms"

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "version",
            name="uq_bom_product_version",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    status: Mapped[BOMStatus] = mapped_column(
        SQLEnum(BOMStatus),
        nullable=False,
        default=BOMStatus.INACTIVE,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
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

    product = relationship(
        "Product",
        foreign_keys=[product_id],
    )

    items = relationship(
        "BOMItem",
        back_populates="bom",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class BOMItem(Base):
    __tablename__ = "bom_items"

    __table_args__ = (
        UniqueConstraint(
            "bom_id",
            "material_id",
            name="uq_bom_material",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    bom_id: Mapped[int] = mapped_column(
        ForeignKey("boms.id"),
        nullable=False,
        index=True,
    )

    material_id: Mapped[int] = mapped_column(
        ForeignKey("raw_materials.id"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
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

    bom = relationship(
        "BOM",
        back_populates="items",
        foreign_keys=[bom_id],
    )

    material = relationship(
        "RawMaterial",
        foreign_keys=[material_id],
    )