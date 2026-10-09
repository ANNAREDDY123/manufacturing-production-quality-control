from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.product import Product, ProductStatus
from app.schemas.product import ProductCreate, ProductUpdate


def create_product(
    db: Session,
    product_data: ProductCreate,
) -> Product:
    existing_product = db.scalar(
        select(Product).where(
            or_(
                Product.product_code == product_data.product_code,
                Product.sku == product_data.sku,
            )
        )
    )

    if existing_product:
        if (
            existing_product.product_code
            == product_data.product_code
        ):
            raise ValueError(
                "Product code already exists"
            )

        raise ValueError(
            "SKU already exists"
        )

    product = Product(
        product_code=product_data.product_code,
        name=product_data.name,
        category=product_data.category,
        sku=product_data.sku,
        unit=product_data.unit,
        standard_production_time=(
            product_data.standard_production_time
        ),
        status=product_data.status,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


def get_product(
    db: Session,
    product_id: int,
) -> Product | None:
    return db.scalar(
        select(Product).where(
            Product.id == product_id
        )
    )


def list_products(
    db: Session,
    search: str | None = None,
    category: str | None = None,
    status: ProductStatus | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Product]:

    query = select(Product)

    if search:
        search_value = f"%{search}%"

        query = query.where(
            or_(
                Product.product_code.ilike(
                    search_value
                ),
                Product.name.ilike(
                    search_value
                ),
                Product.sku.ilike(
                    search_value
                ),
            )
        )

    if category:
        query = query.where(
            Product.category.ilike(category)
        )

    if status:
        query = query.where(
            Product.status == status
        )

    query = (
        query
        .order_by(Product.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(
        db.scalars(query).all()
    )


def update_product(
    db: Session,
    product: Product,
    product_data: ProductUpdate,
) -> Product:

    update_data = product_data.model_dump(
        exclude_unset=True
    )

    if "sku" in update_data:
        existing_sku = db.scalar(
            select(Product).where(
                Product.sku == update_data["sku"],
                Product.id != product.id,
            )
        )

        if existing_sku:
            raise ValueError(
                "SKU already exists"
            )

    for field, value in update_data.items():
        setattr(
            product,
            field,
            value,
        )

    db.commit()
    db.refresh(product)

    return product


def update_product_status(
    db: Session,
    product: Product,
    status: ProductStatus,
) -> Product:

    product.status = status

    db.commit()
    db.refresh(product)

    return product


def delete_product(
    db: Session,
    product: Product,
) -> None:

    db.delete(product)
    db.commit()