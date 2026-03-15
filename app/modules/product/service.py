import uuid

from sqlmodel import Session, select

from app.modules.product.models import (
    SKU,
    Category,
    CategoryCreate,
    FundLimit,
    FundLimitCreate,
    GiftTemplate,
    GiftTemplateCreate,
    Product,
    ProductCreate,
    SKUCreate,
)

# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------


def list_categories(
    *, session: Session, store_id: uuid.UUID | None = None
) -> list[Category]:
    statement = select(Category).order_by(Category.sort_order, Category.created_at)
    if store_id:
        statement = statement.where(Category.store_id == store_id)
    return list(session.exec(statement).all())


def get_category_by_id(*, session: Session, category_id: uuid.UUID) -> Category | None:
    return session.get(Category, category_id)


def create_category(*, session: Session, body: CategoryCreate) -> Category:
    category = Category.model_validate(body)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def update_category(*, session: Session, category: Category, data: dict) -> Category:
    from app.models.base import get_datetime_utc

    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(category, key, value)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def delete_category(*, session: Session, category: Category) -> None:
    session.delete(category)
    session.commit()


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------


def list_products(
    *,
    session: Session,
    store_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
) -> list[Product]:
    statement = select(Product).order_by(Product.created_at)
    if store_id:
        statement = statement.where(Product.store_id == store_id)
    if category_id:
        statement = statement.where(Product.category_id == category_id)
    return list(session.exec(statement).all())


def get_product_by_id(*, session: Session, product_id: uuid.UUID) -> Product | None:
    return session.get(Product, product_id)


def get_product_by_code(
    *, session: Session, store_id: uuid.UUID, code: str
) -> Product | None:
    return session.exec(
        select(Product)
        .where(Product.store_id == store_id)
        .where(Product.code == code)
    ).first()


def create_product(*, session: Session, body: ProductCreate) -> Product:
    product = Product.model_validate(body)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def update_product(*, session: Session, product: Product, data: dict) -> Product:
    from app.models.base import get_datetime_utc

    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(product, key, value)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def delete_product(*, session: Session, product: Product) -> None:
    session.delete(product)
    session.commit()


# ---------------------------------------------------------------------------
# SKU
# ---------------------------------------------------------------------------


def list_skus(
    *, session: Session, product_id: uuid.UUID | None = None
) -> list[SKU]:
    statement = select(SKU).order_by(SKU.created_at)
    if product_id:
        statement = statement.where(SKU.product_id == product_id)
    return list(session.exec(statement).all())


def get_sku_by_id(*, session: Session, sku_id: uuid.UUID) -> SKU | None:
    return session.get(SKU, sku_id)


def get_sku_by_code(
    *, session: Session, product_id: uuid.UUID, sku_code: str
) -> SKU | None:
    return session.exec(
        select(SKU)
        .where(SKU.product_id == product_id)
        .where(SKU.sku_code == sku_code)
    ).first()


def create_sku(*, session: Session, body: SKUCreate) -> SKU:
    sku = SKU.model_validate(body)
    session.add(sku)
    session.commit()
    session.refresh(sku)
    return sku


def update_sku(*, session: Session, sku: SKU, data: dict) -> SKU:
    from app.models.base import get_datetime_utc

    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(sku, key, value)
    session.add(sku)
    session.commit()
    session.refresh(sku)
    return sku


def delete_sku(*, session: Session, sku: SKU) -> None:
    session.delete(sku)
    session.commit()


# ---------------------------------------------------------------------------
# FundLimit
# ---------------------------------------------------------------------------


def list_fund_limits(
    *, session: Session, store_id: uuid.UUID | None = None
) -> list[FundLimit]:
    statement = select(FundLimit).order_by(FundLimit.created_at)
    if store_id:
        statement = statement.where(FundLimit.store_id == store_id)
    return list(session.exec(statement).all())


def get_fund_limit_by_id(
    *, session: Session, fund_limit_id: uuid.UUID
) -> FundLimit | None:
    return session.get(FundLimit, fund_limit_id)


def create_fund_limit(*, session: Session, body: FundLimitCreate) -> FundLimit:
    fund_limit = FundLimit.model_validate(body)
    session.add(fund_limit)
    session.commit()
    session.refresh(fund_limit)
    return fund_limit


def update_fund_limit(
    *, session: Session, fund_limit: FundLimit, data: dict
) -> FundLimit:
    from app.models.base import get_datetime_utc

    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(fund_limit, key, value)
    session.add(fund_limit)
    session.commit()
    session.refresh(fund_limit)
    return fund_limit


def delete_fund_limit(*, session: Session, fund_limit: FundLimit) -> None:
    session.delete(fund_limit)
    session.commit()


# ---------------------------------------------------------------------------
# GiftTemplate
# ---------------------------------------------------------------------------


def list_gift_templates(
    *, session: Session, store_id: uuid.UUID | None = None
) -> list[GiftTemplate]:
    statement = select(GiftTemplate).order_by(GiftTemplate.created_at)
    if store_id:
        statement = statement.where(GiftTemplate.store_id == store_id)
    return list(session.exec(statement).all())


def get_gift_template_by_id(
    *, session: Session, gift_template_id: uuid.UUID
) -> GiftTemplate | None:
    return session.get(GiftTemplate, gift_template_id)


def create_gift_template(*, session: Session, body: GiftTemplateCreate) -> GiftTemplate:
    gift_template = GiftTemplate.model_validate(body)
    session.add(gift_template)
    session.commit()
    session.refresh(gift_template)
    return gift_template


def update_gift_template(
    *, session: Session, gift_template: GiftTemplate, data: dict
) -> GiftTemplate:
    from app.models.base import get_datetime_utc

    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(gift_template, key, value)
    session.add(gift_template)
    session.commit()
    session.refresh(gift_template)
    return gift_template


def delete_gift_template(*, session: Session, gift_template: GiftTemplate) -> None:
    session.delete(gift_template)
    session.commit()
