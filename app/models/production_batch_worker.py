from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ProductionBatchWorker(Base):
    __tablename__ = "production_batch_workers"

    __table_args__ = (
        UniqueConstraint(
            "batch_id",
            "worker_id",
            name="uq_batch_worker",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    batch_id: Mapped[int] = mapped_column(
        ForeignKey(
            "production_batches.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    worker_id: Mapped[int] = mapped_column(
        ForeignKey(
            "workers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )