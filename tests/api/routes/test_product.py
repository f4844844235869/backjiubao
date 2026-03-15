"""Tests for Product Center (商品中心) module."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.modules.product.models import (
    PRICE_DISPLAY_MODE_BOTH,
    PRICE_DISPLAY_MODE_GROSS,
    PRICE_DISPLAY_MODE_NET,
)
from app.modules.product.service import (
    create_category,
    create_fund_limit,
    create_gift_template,
    create_product,
    create_sku,
    get_product_by_code,
    get_sku_by_code,
    list_categories,
    list_skus,
)
from app.modules.store.models import Store
from tests.utils.utils import random_lower_string


def _make_store(db: Session) -> Store:
    store = Store(code=f"prd_{random_lower_string()[:8]}", name="商品测试门店")
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------


def test_create_category(db: Session) -> None:
    store = _make_store(db)
    from app.modules.product.models import CategoryCreate

    cat = create_category(
        session=db,
        body=CategoryCreate(store_id=store.id, name="酒水", sort_order=1, is_active=True),
    )
    assert cat.id is not None
    assert cat.name == "酒水"
    assert cat.store_id == store.id


def test_list_categories_filtered_by_store(db: Session) -> None:
    store = _make_store(db)
    from app.modules.product.models import CategoryCreate

    create_category(session=db, body=CategoryCreate(store_id=store.id, name="分类A"))
    create_category(session=db, body=CategoryCreate(store_id=store.id, name="分类B"))
    cats = list_categories(session=db, store_id=store.id)
    assert len(cats) >= 2
    assert all(c.store_id == store.id for c in cats)


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------


def test_create_product(db: Session) -> None:
    store = _make_store(db)
    from app.modules.product.models import ProductCreate

    product = create_product(
        session=db,
        body=ProductCreate(
            store_id=store.id,
            code="WINE001",
            name="茅台",
            selling_price=Decimal("1899.00"),
            cost_price=Decimal("1200.00"),
            net_profit_price=Decimal("600.00"),
            price_display_mode=PRICE_DISPLAY_MODE_BOTH,
        ),
    )
    assert product.id is not None
    assert product.code == "WINE001"
    assert product.selling_price == Decimal("1899.00")
    assert product.price_display_mode == PRICE_DISPLAY_MODE_BOTH


def test_product_code_unique_per_store(db: Session) -> None:
    store = _make_store(db)
    from app.modules.product.models import ProductCreate

    create_product(
        session=db,
        body=ProductCreate(
            store_id=store.id,
            code="WINE002",
            name="五粮液",
            selling_price=Decimal("999.00"),
        ),
    )
    existing = get_product_by_code(session=db, store_id=store.id, code="WINE002")
    assert existing is not None
    assert existing.name == "五粮液"


def test_product_price_display_modes(db: Session) -> None:
    store = _make_store(db)
    from app.modules.product.models import ProductCreate

    for mode in [PRICE_DISPLAY_MODE_NET, PRICE_DISPLAY_MODE_GROSS, PRICE_DISPLAY_MODE_BOTH]:
        product = create_product(
            session=db,
            body=ProductCreate(
                store_id=store.id,
                code=f"WINE_{mode[:3]}_{random_lower_string()[:4]}",
                name=f"商品_{mode}",
                price_display_mode=mode,
            ),
        )
        assert product.price_display_mode == mode


# ---------------------------------------------------------------------------
# SKU
# ---------------------------------------------------------------------------


def test_create_sku(db: Session) -> None:
    store = _make_store(db)
    from app.modules.product.models import ProductCreate, SKUCreate

    product = create_product(
        session=db,
        body=ProductCreate(store_id=store.id, code="BEER001", name="青岛啤酒"),
    )
    sku = create_sku(
        session=db,
        body=SKUCreate(
            product_id=product.id,
            sku_code="BEER001-500ML",
            spec_name="500ml 瓶装",
            price=Decimal("12.00"),
            cost_price=Decimal("7.00"),
            net_profit_price=Decimal("4.50"),
            price_display_mode=PRICE_DISPLAY_MODE_NET,
        ),
    )
    assert sku.id is not None
    assert sku.sku_code == "BEER001-500ML"
    assert sku.price_display_mode == PRICE_DISPLAY_MODE_NET

    existing = get_sku_by_code(
        session=db, product_id=product.id, sku_code="BEER001-500ML"
    )
    assert existing is not None


def test_list_skus_by_product(db: Session) -> None:
    store = _make_store(db)
    from app.modules.product.models import ProductCreate, SKUCreate

    product = create_product(
        session=db,
        body=ProductCreate(store_id=store.id, code="BEER002", name="雪花啤酒"),
    )
    create_sku(
        session=db,
        body=SKUCreate(product_id=product.id, sku_code="BEER002-330", spec_name="330ml"),
    )
    create_sku(
        session=db,
        body=SKUCreate(product_id=product.id, sku_code="BEER002-500", spec_name="500ml"),
    )
    skus = list_skus(session=db, product_id=product.id)
    assert len(skus) >= 2


# ---------------------------------------------------------------------------
# FundLimit
# ---------------------------------------------------------------------------


def test_create_fund_limit(db: Session) -> None:
    store = _make_store(db)
    from app.modules.product.models import FundLimitCreate

    fl = create_fund_limit(
        session=db,
        body=FundLimitCreate(
            store_id=store.id,
            name="单次消费上限",
            limit_type="SINGLE",
            amount=Decimal("5000.00"),
            is_active=True,
        ),
    )
    assert fl.id is not None
    assert fl.amount == Decimal("5000.00")
    assert fl.limit_type == "SINGLE"


# ---------------------------------------------------------------------------
# GiftTemplate
# ---------------------------------------------------------------------------


def test_create_gift_template(db: Session) -> None:
    store = _make_store(db)
    from app.modules.product.models import GiftTemplateCreate

    gt = create_gift_template(
        session=db,
        body=GiftTemplateCreate(
            store_id=store.id,
            name="充值满100送20",
            gift_type="AMOUNT",
            gift_amount=Decimal("20.00"),
            is_active=True,
        ),
    )
    assert gt.id is not None
    assert gt.gift_amount == Decimal("20.00")


# ---------------------------------------------------------------------------
# API endpoint tests (superuser)
# ---------------------------------------------------------------------------


def test_product_category_api(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    store = _make_store(db)
    payload = {"store_id": str(store.id), "name": "API分类测试", "sort_order": 0}
    resp = client.post(
        "/api/v1/product/categories",
        json=payload,
        headers=superuser_token_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "SUCCESS"
    assert data["data"]["name"] == "API分类测试"
    cat_id = data["data"]["id"]

    # List
    resp = client.get("/api/v1/product/categories", headers=superuser_token_headers)
    assert resp.status_code == 200

    # Update
    resp = client.patch(
        f"/api/v1/product/categories/{cat_id}",
        json={"name": "API分类更新"},
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "API分类更新"

    # Delete
    resp = client.delete(
        f"/api/v1/product/categories/{cat_id}",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200


def test_product_api_create_and_list(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    store = _make_store(db)
    payload = {
        "store_id": str(store.id),
        "code": f"API_{random_lower_string()[:6]}",
        "name": "API商品测试",
        "selling_price": "199.00",
        "cost_price": "100.00",
        "net_profit_price": "80.00",
        "price_display_mode": "BOTH",
    }
    resp = client.post(
        "/api/v1/product/products",
        json=payload,
        headers=superuser_token_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "SUCCESS"
    assert data["data"]["price_display_mode"] == "BOTH"
