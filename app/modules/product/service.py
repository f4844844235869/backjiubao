import uuid

from sqlmodel import Session, select

from app.models.base import get_datetime_utc
from app.modules.product.models import (
    Product,
    ProductCategory,
    ProductCategoryCreate,
    ProductCreate,
    ProductSku,
    ProductSkuCreate,
    SkuInventoryMapping,
    SkuInventoryMappingCreate,
    StoreProduct,
    StoreProductCreate,
    StoreProductSku,
    StoreProductSkuCreate,
)

# ---------------------------------------------------------------------------
# ProductCategory
# ---------------------------------------------------------------------------


def list_product_categories(*, session: Session) -> list[ProductCategory]:
    statement = select(ProductCategory).where(
        ProductCategory.is_deleted.is_(False)
    ).order_by(ProductCategory.sort_order.asc())
    return list(session.exec(statement).all())


def get_product_category_by_id(
    *, session: Session, category_id: uuid.UUID
) -> ProductCategory | None:
    return session.get(ProductCategory, category_id)


def get_product_category_by_code(
    *, session: Session, code: str
) -> ProductCategory | None:
    return session.exec(
        select(ProductCategory).where(ProductCategory.code == code)
    ).first()


def create_product_category(
    *, session: Session, body: ProductCategoryCreate
) -> ProductCategory:
    category = ProductCategory.model_validate(body)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def update_product_category(
    *,
    session: Session,
    category: ProductCategory,
    data: dict,
) -> ProductCategory:
    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(category, key, value)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def has_child_categories(*, session: Session, category_id: uuid.UUID) -> bool:
    return (
        session.exec(
            select(ProductCategory).where(
                ProductCategory.parent_id == category_id,
                ProductCategory.is_deleted.is_(False),
            )
        ).first()
        is not None
    )


def has_products_in_category(*, session: Session, category_id: uuid.UUID) -> bool:
    return (
        session.exec(
            select(Product).where(
                Product.category_id == category_id,
                Product.is_deleted.is_(False),
            )
        ).first()
        is not None
    )


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------


def list_products(
    *,
    session: Session,
    category_id: uuid.UUID | None = None,
    is_active: bool | None = None,
) -> list[Product]:
    statement = select(Product).where(Product.is_deleted.is_(False))
    if category_id is not None:
        statement = statement.where(Product.category_id == category_id)
    if is_active is not None:
        statement = statement.where(Product.is_active.is_(is_active))
    statement = statement.order_by(Product.created_at.desc())
    return list(session.exec(statement).all())


def get_product_by_id(*, session: Session, product_id: uuid.UUID) -> Product | None:
    return session.get(Product, product_id)


def get_product_by_code(*, session: Session, code: str) -> Product | None:
    return session.exec(
        select(Product).where(Product.code == code)
    ).first()


def create_product(*, session: Session, body: ProductCreate) -> Product:
    product = Product.model_validate(body)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def update_product(
    *, session: Session, product: Product, data: dict
) -> Product:
    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(product, key, value)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


# ---------------------------------------------------------------------------
# ProductSku
# ---------------------------------------------------------------------------


def list_product_skus(
    *, session: Session, product_id: uuid.UUID
) -> list[ProductSku]:
    statement = (
        select(ProductSku)
        .where(ProductSku.product_id == product_id)
        .where(ProductSku.is_deleted.is_(False))
        .order_by(ProductSku.created_at.asc())
    )
    return list(session.exec(statement).all())


def get_product_sku_by_id(
    *, session: Session, sku_id: uuid.UUID
) -> ProductSku | None:
    return session.get(ProductSku, sku_id)


def get_product_sku_by_code(*, session: Session, code: str) -> ProductSku | None:
    return session.exec(
        select(ProductSku).where(ProductSku.code == code)
    ).first()


def create_product_sku(*, session: Session, body: ProductSkuCreate) -> ProductSku:
    sku = ProductSku.model_validate(body)
    session.add(sku)
    session.commit()
    session.refresh(sku)
    return sku


def update_product_sku(
    *, session: Session, sku: ProductSku, data: dict
) -> ProductSku:
    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(sku, key, value)
    session.add(sku)
    session.commit()
    session.refresh(sku)
    return sku


# ---------------------------------------------------------------------------
# StoreProduct
# ---------------------------------------------------------------------------


def list_store_products(
    *, session: Session, store_id: uuid.UUID
) -> list[StoreProduct]:
    statement = (
        select(StoreProduct)
        .where(StoreProduct.store_id == store_id)
        .order_by(StoreProduct.sort_order.asc())
    )
    return list(session.exec(statement).all())


def get_store_product(
    *, session: Session, store_id: uuid.UUID, product_id: uuid.UUID
) -> StoreProduct | None:
    return session.exec(
        select(StoreProduct).where(
            StoreProduct.store_id == store_id,
            StoreProduct.product_id == product_id,
        )
    ).first()


def get_store_product_by_id(
    *, session: Session, store_product_id: uuid.UUID
) -> StoreProduct | None:
    return session.get(StoreProduct, store_product_id)


def create_store_product(
    *, session: Session, body: StoreProductCreate
) -> StoreProduct:
    sp = StoreProduct.model_validate(body)
    session.add(sp)
    session.commit()
    session.refresh(sp)
    return sp


def update_store_product(
    *, session: Session, store_product: StoreProduct, data: dict
) -> StoreProduct:
    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(store_product, key, value)
    session.add(store_product)
    session.commit()
    session.refresh(store_product)
    return store_product


# ---------------------------------------------------------------------------
# StoreProductSku
# ---------------------------------------------------------------------------


def list_store_product_skus(
    *, session: Session, store_id: uuid.UUID, product_id: uuid.UUID | None = None
) -> list[StoreProductSku]:
    statement = select(StoreProductSku).where(
        StoreProductSku.store_id == store_id
    )
    if product_id is not None:
        statement = statement.where(StoreProductSku.product_id == product_id)
    return list(session.exec(statement).all())


def get_store_product_sku(
    *, session: Session, store_id: uuid.UUID, sku_id: uuid.UUID
) -> StoreProductSku | None:
    return session.exec(
        select(StoreProductSku).where(
            StoreProductSku.store_id == store_id,
            StoreProductSku.sku_id == sku_id,
        )
    ).first()


def get_store_product_sku_by_id(
    *, session: Session, store_product_sku_id: uuid.UUID
) -> StoreProductSku | None:
    return session.get(StoreProductSku, store_product_sku_id)


def create_store_product_sku(
    *, session: Session, body: StoreProductSkuCreate
) -> StoreProductSku:
    sps = StoreProductSku.model_validate(body)
    session.add(sps)
    session.commit()
    session.refresh(sps)
    return sps


def update_store_product_sku(
    *, session: Session, store_product_sku: StoreProductSku, data: dict
) -> StoreProductSku:
    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(store_product_sku, key, value)
    session.add(store_product_sku)
    session.commit()
    session.refresh(store_product_sku)
    return store_product_sku


# ---------------------------------------------------------------------------
# SkuInventoryMapping
# ---------------------------------------------------------------------------


def list_sku_inventory_mappings(
    *, session: Session, sku_id: uuid.UUID
) -> list[SkuInventoryMapping]:
    statement = (
        select(SkuInventoryMapping)
        .where(SkuInventoryMapping.sku_id == sku_id)
        .order_by(SkuInventoryMapping.sort_order.asc())
    )
    return list(session.exec(statement).all())


def get_sku_inventory_mapping_by_id(
    *, session: Session, mapping_id: uuid.UUID
) -> SkuInventoryMapping | None:
    return session.get(SkuInventoryMapping, mapping_id)


def create_sku_inventory_mapping(
    *, session: Session, body: SkuInventoryMappingCreate
) -> SkuInventoryMapping:
    mapping = SkuInventoryMapping.model_validate(body)
    session.add(mapping)
    session.commit()
    session.refresh(mapping)
    return mapping


def update_sku_inventory_mapping(
    *, session: Session, mapping: SkuInventoryMapping, data: dict
) -> SkuInventoryMapping:
    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(mapping, key, value)
    session.add(mapping)
    session.commit()
    session.refresh(mapping)
    return mapping


def delete_sku_inventory_mapping(
    *, session: Session, mapping: SkuInventoryMapping
) -> None:
    session.delete(mapping)
    session.commit()
