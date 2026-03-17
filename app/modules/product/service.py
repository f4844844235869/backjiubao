import itertools
import uuid
from collections.abc import Iterable

from sqlmodel import Session, select

from app.models.base import get_datetime_utc
from app.modules.product.models import (
    DISPLAY_TYPE_SELECT,
    Product,
    ProductAttribute,
    ProductAttributeAssignment,
    ProductAttributeAssignmentCreate,
    ProductAttributeAssignmentValue,
    ProductAttributeAssignmentValueCreate,
    ProductAttributeCreate,
    ProductAttributeValue,
    ProductAttributeValueCreate,
    ProductCategory,
    ProductCategoryCreate,
    ProductCreate,
    ProductSku,
    ProductSkuAttributeValue,
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
    return session.exec(select(Product).where(Product.code == code)).first()


def create_product(*, session: Session, body: ProductCreate) -> Product:
    product = Product.model_validate(body)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def update_product(*, session: Session, product: Product, data: dict) -> Product:
    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(product, key, value)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


# ---------------------------------------------------------------------------
# ProductAttribute
# ---------------------------------------------------------------------------


def list_product_attributes(*, session: Session) -> list[ProductAttribute]:
    statement = select(ProductAttribute).order_by(ProductAttribute.sort_order.asc())
    return list(session.exec(statement).all())


def get_product_attribute_by_id(
    *, session: Session, attribute_id: uuid.UUID
) -> ProductAttribute | None:
    return session.get(ProductAttribute, attribute_id)


def get_product_attribute_by_code(
    *, session: Session, code: str
) -> ProductAttribute | None:
    return session.exec(
        select(ProductAttribute).where(ProductAttribute.code == code)
    ).first()


def create_product_attribute(
    *, session: Session, body: ProductAttributeCreate
) -> ProductAttribute:
    attribute = ProductAttribute.model_validate(body)
    if not attribute.display_type:
        attribute.display_type = DISPLAY_TYPE_SELECT
    session.add(attribute)
    session.commit()
    session.refresh(attribute)
    return attribute


def update_product_attribute(
    *, session: Session, attribute: ProductAttribute, data: dict
) -> ProductAttribute:
    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(attribute, key, value)
    session.add(attribute)
    session.commit()
    session.refresh(attribute)
    return attribute


def list_product_attribute_values(
    *, session: Session, attribute_id: uuid.UUID
) -> list[ProductAttributeValue]:
    statement = (
        select(ProductAttributeValue)
        .where(ProductAttributeValue.attribute_id == attribute_id)
        .order_by(ProductAttributeValue.sort_order.asc())
    )
    return list(session.exec(statement).all())


def get_product_attribute_value_by_id(
    *, session: Session, attribute_value_id: uuid.UUID
) -> ProductAttributeValue | None:
    return session.get(ProductAttributeValue, attribute_value_id)


def get_product_attribute_value_by_code(
    *, session: Session, attribute_id: uuid.UUID, code: str
) -> ProductAttributeValue | None:
    return session.exec(
        select(ProductAttributeValue).where(
            ProductAttributeValue.attribute_id == attribute_id,
            ProductAttributeValue.code == code,
        )
    ).first()


def create_product_attribute_value(
    *, session: Session, body: ProductAttributeValueCreate
) -> ProductAttributeValue:
    value = ProductAttributeValue.model_validate(body)
    session.add(value)
    session.commit()
    session.refresh(value)
    return value


def update_product_attribute_value(
    *,
    session: Session,
    attribute_value: ProductAttributeValue,
    data: dict,
) -> ProductAttributeValue:
    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(attribute_value, key, value)
    session.add(attribute_value)
    session.commit()
    session.refresh(attribute_value)
    return attribute_value


def list_product_attribute_assignments(
    *, session: Session, product_id: uuid.UUID
) -> list[ProductAttributeAssignment]:
    statement = (
        select(ProductAttributeAssignment)
        .where(ProductAttributeAssignment.product_id == product_id)
        .order_by(ProductAttributeAssignment.sort_order.asc())
    )
    return list(session.exec(statement).all())


def get_product_attribute_assignment_by_id(
    *, session: Session, assignment_id: uuid.UUID
) -> ProductAttributeAssignment | None:
    return session.get(ProductAttributeAssignment, assignment_id)


def get_product_attribute_assignment(
    *, session: Session, product_id: uuid.UUID, attribute_id: uuid.UUID
) -> ProductAttributeAssignment | None:
    return session.exec(
        select(ProductAttributeAssignment).where(
            ProductAttributeAssignment.product_id == product_id,
            ProductAttributeAssignment.attribute_id == attribute_id,
        )
    ).first()


def create_product_attribute_assignment(
    *, session: Session, body: ProductAttributeAssignmentCreate
) -> ProductAttributeAssignment:
    assignment = ProductAttributeAssignment.model_validate(body)
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return assignment


def update_product_attribute_assignment(
    *,
    session: Session,
    assignment: ProductAttributeAssignment,
    data: dict,
) -> ProductAttributeAssignment:
    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(assignment, key, value)
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return assignment


def list_product_attribute_assignment_values(
    *, session: Session, assignment_id: uuid.UUID
) -> list[ProductAttributeAssignmentValue]:
    statement = (
        select(ProductAttributeAssignmentValue)
        .where(ProductAttributeAssignmentValue.assignment_id == assignment_id)
        .order_by(ProductAttributeAssignmentValue.sort_order.asc())
    )
    return list(session.exec(statement).all())


def get_product_attribute_assignment_value_by_id(
    *, session: Session, assignment_value_id: uuid.UUID
) -> ProductAttributeAssignmentValue | None:
    return session.get(ProductAttributeAssignmentValue, assignment_value_id)


def get_product_attribute_assignment_value(
    *, session: Session, assignment_id: uuid.UUID, attribute_value_id: uuid.UUID
) -> ProductAttributeAssignmentValue | None:
    return session.exec(
        select(ProductAttributeAssignmentValue).where(
            ProductAttributeAssignmentValue.assignment_id == assignment_id,
            ProductAttributeAssignmentValue.attribute_value_id == attribute_value_id,
        )
    ).first()


def create_product_attribute_assignment_value(
    *, session: Session, body: ProductAttributeAssignmentValueCreate
) -> ProductAttributeAssignmentValue:
    assignment_value = ProductAttributeAssignmentValue.model_validate(body)
    session.add(assignment_value)
    session.commit()
    session.refresh(assignment_value)
    return assignment_value


def delete_product_attribute_assignment_value(
    *, session: Session, assignment_value: ProductAttributeAssignmentValue
) -> None:
    session.delete(assignment_value)
    session.commit()


# ---------------------------------------------------------------------------
# ProductSku
# ---------------------------------------------------------------------------


def list_product_skus(*, session: Session, product_id: uuid.UUID) -> list[ProductSku]:
    statement = (
        select(ProductSku)
        .where(ProductSku.product_id == product_id)
        .where(ProductSku.is_deleted.is_(False))
        .order_by(ProductSku.created_at.asc())
    )
    return list(session.exec(statement).all())


def list_all_product_skus(
    *, session: Session, product_id: uuid.UUID
) -> list[ProductSku]:
    statement = (
        select(ProductSku)
        .where(ProductSku.product_id == product_id)
        .order_by(ProductSku.created_at.asc())
    )
    return list(session.exec(statement).all())


def get_product_sku_by_id(*, session: Session, sku_id: uuid.UUID) -> ProductSku | None:
    return session.get(ProductSku, sku_id)


def get_product_sku_by_code(*, session: Session, code: str) -> ProductSku | None:
    return session.exec(select(ProductSku).where(ProductSku.code == code)).first()


def list_product_sku_attribute_values(
    *, session: Session, sku_id: uuid.UUID
) -> list[ProductSkuAttributeValue]:
    statement = (
        select(ProductSkuAttributeValue)
        .where(ProductSkuAttributeValue.sku_id == sku_id)
        .order_by(ProductSkuAttributeValue.attribute_id.asc())
    )
    return list(session.exec(statement).all())


def list_product_sku_attribute_values_by_sku_ids(
    *, session: Session, sku_ids: Iterable[uuid.UUID]
) -> list[ProductSkuAttributeValue]:
    ids = list(sku_ids)
    if not ids:
        return []
    statement = select(ProductSkuAttributeValue).where(
        ProductSkuAttributeValue.sku_id.in_(ids)
    )
    return list(session.exec(statement).all())


def product_has_attribute_assignments(
    *, session: Session, product_id: uuid.UUID
) -> bool:
    return (
        session.exec(
            select(ProductAttributeAssignment).where(
                ProductAttributeAssignment.product_id == product_id
            )
        ).first()
        is not None
    )


def _next_sku_code(*, session: Session, product: Product) -> str:
    statement = select(ProductSku).where(ProductSku.product_id == product.id)
    existing_count = len(list(session.exec(statement).all()))
    sequence = existing_count + 1
    while True:
        code = f"{product.code}-{sequence:02d}"
        existing = get_product_sku_by_code(session=session, code=code)
        if not existing:
            return code
        sequence += 1


def _apply_default_state(
    *,
    session: Session,
    sku: ProductSku,
    requested_default: bool | None = None,
) -> None:
    if requested_default:
        statement = select(ProductSku).where(
            ProductSku.product_id == sku.product_id,
            ProductSku.id != sku.id,
            ProductSku.is_default.is_(True),
            ProductSku.is_deleted.is_(False),
        )
        for sibling in session.exec(statement).all():
            sibling.is_default = False
            sibling.updated_at = get_datetime_utc()
            session.add(sibling)
        sku.is_default = True
        return

    current_default = session.exec(
        select(ProductSku).where(
            ProductSku.product_id == sku.product_id,
            ProductSku.is_default.is_(True),
            ProductSku.is_deleted.is_(False),
        )
    ).first()
    if current_default is None:
        sku.is_default = True


def ensure_default_sku_for_product(
    *, session: Session, product_id: uuid.UUID
) -> ProductSku | None:
    default_sku = session.exec(
        select(ProductSku).where(
            ProductSku.product_id == product_id,
            ProductSku.is_default.is_(True),
            ProductSku.is_deleted.is_(False),
            ProductSku.is_active.is_(True),
        )
    ).first()
    if default_sku:
        return default_sku

    candidate = session.exec(
        select(ProductSku)
        .where(
            ProductSku.product_id == product_id,
            ProductSku.is_deleted.is_(False),
            ProductSku.is_active.is_(True),
        )
        .order_by(ProductSku.created_at.asc())
    ).first()
    if candidate:
        candidate.is_default = True
        candidate.updated_at = get_datetime_utc()
        session.add(candidate)
        session.commit()
        session.refresh(candidate)
    return candidate


def create_product_sku(*, session: Session, body: ProductSkuCreate) -> ProductSku:
    product = get_product_by_id(session=session, product_id=body.product_id)
    if product is None:
        raise ValueError("product not found")

    sku = ProductSku(
        product_id=body.product_id,
        code=body.code or _next_sku_code(session=session, product=product),
        name=body.name or product.name,
        spec_text=body.spec_text,
        suggested_price=body.suggested_price
        if body.suggested_price is not None
        else product.suggested_price,
        barcode=body.barcode,
        is_default=body.is_default,
        fund_usage_type=body.fund_usage_type,
        is_inventory_item=body.is_inventory_item,
        is_commission_enabled=body.is_commission_enabled,
        commission_type=body.commission_type,
        commission_value=body.commission_value,
        is_profit_enabled=body.is_profit_enabled,
        standard_cost_price=body.standard_cost_price,
        inventory_mode=body.inventory_mode,
        allow_negative_inventory=body.allow_negative_inventory,
        is_sale_enabled=body.is_sale_enabled,
        is_active=body.is_active,
        is_deleted=False,
    )
    _apply_default_state(
        session=session,
        sku=sku,
        requested_default=body.is_default,
    )
    session.add(sku)
    session.commit()
    session.refresh(sku)
    return sku


def update_product_sku(*, session: Session, sku: ProductSku, data: dict) -> ProductSku:
    requested_default = data.pop("is_default", None) if "is_default" in data else None
    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(sku, key, value)
    if requested_default is not None:
        if requested_default:
            _apply_default_state(session=session, sku=sku, requested_default=True)
        else:
            sku.is_default = False
    session.add(sku)
    session.commit()
    session.refresh(sku)
    ensure_default_sku_for_product(session=session, product_id=sku.product_id)
    session.refresh(sku)
    return sku


def build_sku_display_name(
    *, assignment_values: list[tuple[ProductAttributeAssignment, ProductAttributeAssignmentValue]]
) -> str:
    return "-".join(item.attribute_value.name for _, item in assignment_values)


def list_effective_product_attribute_assignments(
    *, session: Session, product_id: uuid.UUID
) -> list[tuple[ProductAttributeAssignment, list[ProductAttributeAssignmentValue]]]:
    assignments = list_product_attribute_assignments(session=session, product_id=product_id)
    result: list[tuple[ProductAttributeAssignment, list[ProductAttributeAssignmentValue]]] = []
    for assignment in assignments:
        values = []
        for assignment_value in list_product_attribute_assignment_values(
            session=session, assignment_id=assignment.id
        ):
            attribute_value = get_product_attribute_value_by_id(
                session=session, attribute_value_id=assignment_value.attribute_value_id
            )
            if attribute_value and attribute_value.is_active:
                values.append(assignment_value)
        result.append((assignment, values))
    return result


def _combo_key_from_pairs(
    pairs: Iterable[tuple[uuid.UUID, uuid.UUID]]
) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((str(attribute_id), str(value_id)) for attribute_id, value_id in pairs))


def _build_existing_combo_map(
    *, session: Session, product_id: uuid.UUID
) -> dict[tuple[tuple[str, str], ...], ProductSku]:
    existing = list_all_product_skus(session=session, product_id=product_id)
    links = list_product_sku_attribute_values_by_sku_ids(
        session=session, sku_ids=[sku.id for sku in existing]
    )
    by_sku: dict[uuid.UUID, list[ProductSkuAttributeValue]] = {}
    for link in links:
        by_sku.setdefault(link.sku_id, []).append(link)

    combo_map: dict[tuple[tuple[str, str], ...], ProductSku] = {}
    for sku in existing:
        sku_links = by_sku.get(sku.id, [])
        if not sku_links:
            continue
        combo_map[_combo_key_from_pairs(
            (link.attribute_id, link.attribute_value_id) for link in sku_links
        )] = sku
    return combo_map


def _set_sku_attribute_values(
    *,
    session: Session,
    sku: ProductSku,
    assignment_values: list[tuple[ProductAttributeAssignment, ProductAttributeAssignmentValue]],
) -> None:
    existing_links = list_product_sku_attribute_values(session=session, sku_id=sku.id)
    for link in existing_links:
        session.delete(link)
    session.flush()
    now = get_datetime_utc()
    for assignment, assignment_value in assignment_values:
        session.add(
            ProductSkuAttributeValue(
                sku_id=sku.id,
                attribute_id=assignment.attribute_id,
                attribute_value_id=assignment_value.attribute_value_id,
                created_at=now,
                updated_at=now,
            )
        )
    session.flush()


def generate_product_skus(
    *, session: Session, product: Product
) -> dict[str, list[ProductSku]]:
    effective_assignments = list_effective_product_attribute_assignments(
        session=session, product_id=product.id
    )
    if not effective_assignments:
        raise ValueError("PRODUCT_HAS_NO_SKU_ATTRIBUTES")

    for _, values in effective_assignments:
        if not values:
            raise ValueError("PRODUCT_ATTRIBUTE_VALUES_REQUIRED")

    all_existing = list_all_product_skus(session=session, product_id=product.id)
    existing_combo_map = _build_existing_combo_map(session=session, product_id=product.id)
    target_keys: list[tuple[tuple[str, str], ...]] = []
    created: list[ProductSku] = []
    retained: list[ProductSku] = []

    for combination in itertools.product(*(values for _, values in effective_assignments)):
        assignment_pairs = list(
            zip(
                [assignment for assignment, _ in effective_assignments],
                combination,
                strict=True,
            )
        )
        combo_key = _combo_key_from_pairs(
            (assignment.attribute_id, assignment_value.attribute_value_id)
            for assignment, assignment_value in assignment_pairs
        )
        target_keys.append(combo_key)

        existing = existing_combo_map.get(combo_key)
        display_name = build_sku_display_name(assignment_values=assignment_pairs)
        if existing:
            existing.name = display_name
            existing.spec_text = display_name
            existing.is_deleted = False
            existing.is_active = True
            existing.updated_at = get_datetime_utc()
            session.add(existing)
            session.flush()
            _set_sku_attribute_values(
                session=session, sku=existing, assignment_values=assignment_pairs
            )
            retained.append(existing)
            continue

        sku = ProductSku(
            product_id=product.id,
            code=_next_sku_code(session=session, product=product),
            name=display_name,
            spec_text=display_name,
            suggested_price=product.suggested_price,
            barcode=None,
            is_default=False,
            fund_usage_type=None,
            is_inventory_item=None,
            is_commission_enabled=None,
            commission_type=None,
            commission_value=None,
            is_profit_enabled=None,
            standard_cost_price=None,
            inventory_mode="NONE",
            allow_negative_inventory=False,
            is_sale_enabled=product.is_sale_enabled,
            is_active=True,
            is_deleted=False,
        )
        session.add(sku)
        session.flush()
        _set_sku_attribute_values(
            session=session, sku=sku, assignment_values=assignment_pairs
        )
        created.append(sku)

    deactivated: list[ProductSku] = []
    kept_ids = {sku.id for sku in retained} | {sku.id for sku in created}
    for sku in all_existing:
        if sku.id in kept_ids or sku.is_deleted:
            continue
        if not sku.is_active and not sku.is_default:
            continue
        sku.is_active = False
        sku.is_default = False
        sku.updated_at = get_datetime_utc()
        session.add(sku)
        deactivated.append(sku)

    if not session.exec(
        select(ProductSku).where(
            ProductSku.product_id == product.id,
            ProductSku.is_default.is_(True),
            ProductSku.is_deleted.is_(False),
            ProductSku.is_active.is_(True),
        )
    ).first():
        ordered_candidates = retained + created
        if ordered_candidates:
            ordered_candidates[0].is_default = True
            ordered_candidates[0].updated_at = get_datetime_utc()
            session.add(ordered_candidates[0])

    session.commit()
    for sku in created + retained + deactivated:
        session.refresh(sku)
    ensure_default_sku_for_product(session=session, product_id=product.id)
    return {
        "created": created,
        "retained": retained,
        "deactivated": deactivated,
    }


# ---------------------------------------------------------------------------
# StoreProduct
# ---------------------------------------------------------------------------


def list_store_products(*, session: Session, store_id: uuid.UUID) -> list[StoreProduct]:
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


def create_store_product(*, session: Session, body: StoreProductCreate) -> StoreProduct:
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
    statement = select(StoreProductSku).where(StoreProductSku.store_id == store_id)
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
