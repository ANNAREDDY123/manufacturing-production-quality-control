from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.production_line import ProductionLine
from app.models.production_order import (
    ProductionOrder,
    ProductionOrderPriority,
    ProductionOrderStatus,
)
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.production_order import (
    ProductionOrderCreate,
    ProductionOrderStatusUpdate,
    ProductionOrderUpdate,
)


VALID_TRANSITIONS = {
    ProductionOrderStatus.DRAFT: {
        ProductionOrderStatus.SCHEDULED,
        ProductionOrderStatus.CANCELLED,
    },
    ProductionOrderStatus.SCHEDULED: {
        ProductionOrderStatus.IN_PROGRESS,
        ProductionOrderStatus.CANCELLED,
    },
    ProductionOrderStatus.IN_PROGRESS: {
        ProductionOrderStatus.PAUSED,
        ProductionOrderStatus.COMPLETED,
        ProductionOrderStatus.CANCELLED,
    },
    ProductionOrderStatus.PAUSED: {
        ProductionOrderStatus.IN_PROGRESS,
        ProductionOrderStatus.CANCELLED,
    },
    ProductionOrderStatus.COMPLETED: set(),
    ProductionOrderStatus.CANCELLED: set(),
}


def _get_order(
    db: Session,
    order_id: int,
) -> ProductionOrder:
    order = db.scalar(
        select(ProductionOrder).where(
            ProductionOrder.id == order_id
        )
    )

    if order is None:
        raise ValueError("Production order not found")

    return order


def _get_product(
    db: Session,
    product_id: int,
) -> Product:
    product = db.scalar(
        select(Product).where(
            Product.id == product_id
        )
    )

    if product is None:
        raise ValueError("Product not found")

    if product.status.value != "Active":
        raise ValueError(
            "Cannot create production order for an inactive product"
        )

    return product


def _get_production_line(
    db: Session,
    production_line_id: int,
) -> ProductionLine:
    line = db.scalar(
        select(ProductionLine).where(
            ProductionLine.id == production_line_id
        )
    )

    if line is None:
        raise ValueError("Production line not found")

    if line.status.value != "Active":
        raise ValueError(
            "Production line is not active"
        )

    return line


def _get_supervisor(
    db: Session,
    supervisor_id: int | None,
) -> User | None:
    if supervisor_id is None:
        return None

    supervisor = db.scalar(
        select(User).where(
            User.id == supervisor_id
        )
    )

    if supervisor is None:
        raise ValueError("Supervisor not found")

    if supervisor.role != UserRole.PRODUCTION_SUPERVISOR:
        raise ValueError(
            "Assigned user must have Production Supervisor role"
        )

    if not supervisor.is_active:
        raise ValueError(
            "Supervisor account is inactive"
        )

    return supervisor


def create_production_order(
    db: Session,
    data: ProductionOrderCreate,
    created_by: int | None = None,
) -> ProductionOrder:
    existing = db.scalar(
        select(ProductionOrder).where(
            ProductionOrder.order_number
            == data.order_number
        )
    )

    if existing:
        raise ValueError(
            "Production order number already exists"
        )

    if data.target_date < date.today():
        raise ValueError(
            "Target date cannot be in the past"
        )

    _get_product(
        db,
        data.product_id,
    )

    _get_production_line(
        db,
        data.production_line_id,
    )

    _get_supervisor(
        db,
        data.supervisor_id,
    )

    order = ProductionOrder(
        order_number=data.order_number,
        product_id=data.product_id,
        quantity=data.quantity,
        target_date=data.target_date,
        production_line_id=data.production_line_id,
        priority=data.priority,
        supervisor_id=data.supervisor_id,
        status=ProductionOrderStatus.DRAFT,
        created_by=created_by,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def get_production_order(
    db: Session,
    order_id: int,
) -> ProductionOrder:
    return _get_order(
        db,
        order_id,
    )


def list_production_orders(
    db: Session,
    search: str | None = None,
    product_id: int | None = None,
    production_line_id: int | None = None,
    status: ProductionOrderStatus | None = None,
    priority: ProductionOrderPriority | None = None,
    supervisor_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[ProductionOrder]:
    query = select(ProductionOrder)

    if search:
        search_value = f"%{search}%"

        query = query.where(
            ProductionOrder.order_number.ilike(
                search_value
            )
        )

    if product_id is not None:
        query = query.where(
            ProductionOrder.product_id
            == product_id
        )

    if production_line_id is not None:
        query = query.where(
            ProductionOrder.production_line_id
            == production_line_id
        )

    if status is not None:
        query = query.where(
            ProductionOrder.status == status
        )

    if priority is not None:
        query = query.where(
            ProductionOrder.priority == priority
        )

    if supervisor_id is not None:
        query = query.where(
            ProductionOrder.supervisor_id
            == supervisor_id
        )

    query = (
        query
        .order_by(ProductionOrder.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(
        db.scalars(query).all()
    )


def update_production_order(
    db: Session,
    order_id: int,
    data: ProductionOrderUpdate,
) -> ProductionOrder:
    order = _get_order(
        db,
        order_id,
    )

    if order.status not in {
        ProductionOrderStatus.DRAFT,
        ProductionOrderStatus.SCHEDULED,
    }:
        raise ValueError(
            "Only Draft or Scheduled orders can be modified"
        )

    if (
        data.target_date is not None
        and data.target_date < date.today()
    ):
        raise ValueError(
            "Target date cannot be in the past"
        )

    if data.quantity is not None:
        order.quantity = data.quantity

    if data.target_date is not None:
        order.target_date = data.target_date

    if data.production_line_id is not None:
        _get_production_line(
            db,
            data.production_line_id,
        )

        order.production_line_id = (
            data.production_line_id
        )

    if data.priority is not None:
        order.priority = data.priority

    if data.supervisor_id is not None:
        _get_supervisor(
            db,
            data.supervisor_id,
        )

        order.supervisor_id = (
            data.supervisor_id
        )

    db.commit()
    db.refresh(order)

    return order


def update_production_order_status(
    db: Session,
    order_id: int,
    data: ProductionOrderStatusUpdate,
) -> ProductionOrder:
    order = _get_order(
        db,
        order_id,
    )

    current_status = order.status
    new_status = data.status

    if current_status == new_status:
        return order

    allowed_statuses = VALID_TRANSITIONS.get(
        current_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise ValueError(
            f"Invalid status transition: "
            f"{current_status.value} -> {new_status.value}"
        )

    order.status = new_status

    db.commit()
    db.refresh(order)

    return order