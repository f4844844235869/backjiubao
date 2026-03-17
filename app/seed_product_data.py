"""
商品中心 Demo 数据初始化脚本

用法:
    uv run python -m app.seed_product_data

幂等设计：重复执行不会产生重复数据。
"""

import logging
from decimal import Decimal

from sqlmodel import Session

from app.core.db import engine
from app.modules.product.models import (
    Product,
    ProductCategory,
    ProductCategoryCreate,
    ProductCreate,
    ProductSku,
    ProductSkuCreate,
    StoreProduct,
    StoreProductCreate,
    StoreProductSku,
    StoreProductSkuCreate,
)
from app.modules.product.service import (
    create_product,
    create_product_category,
    create_product_sku,
    create_store_product,
    create_store_product_sku,
    get_product_by_code,
    get_product_category_by_code,
    get_product_sku_by_code,
    get_store_product,
    get_store_product_sku,
)
from app.modules.store.service import get_store_by_code

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 分类定义
# ---------------------------------------------------------------------------
CATEGORY_DEFS = [
    # 一级分类
    {"code": "CAT-DRINKS", "name": "酒水饮料", "level": 1, "parent_code": None, "sort_order": 1},
    {"code": "CAT-FOOD",   "name": "小食甜品", "level": 1, "parent_code": None, "sort_order": 2},
    # 二级分类
    {"code": "CAT-BEER",    "name": "啤酒",     "level": 2, "parent_code": "CAT-DRINKS", "sort_order": 1},
    {"code": "CAT-SPIRITS", "name": "烈酒",     "level": 2, "parent_code": "CAT-DRINKS", "sort_order": 2},
    {"code": "CAT-SNACK",   "name": "小吃拼盘", "level": 2, "parent_code": "CAT-FOOD",   "sort_order": 1},
]

# ---------------------------------------------------------------------------
# 商品 & SKU 定义
# ---------------------------------------------------------------------------
# 每条商品记录：code / name / category_code / unit / suggested_price / product_type
# skus: list of {code, name, spec_text, is_default, suggested_price}
PRODUCT_DEFS = [
    {
        "code": "PRD-BEER-001",
        "name": "青岛啤酒",
        "category_code": "CAT-BEER",
        "unit": "瓶",
        "suggested_price": Decimal("18.00"),
        "product_type": "NORMAL",
        "is_storable": True,
        "skus": [
            {"code": "SKU-BEER-001-330", "name": "330ml单瓶", "spec_text": "330ml", "is_default": True,  "suggested_price": Decimal("18.00")},
            {"code": "SKU-BEER-001-500", "name": "500ml单瓶", "spec_text": "500ml", "is_default": False, "suggested_price": Decimal("22.00")},
        ],
    },
    {
        "code": "PRD-BEER-002",
        "name": "喜力啤酒",
        "category_code": "CAT-BEER",
        "unit": "瓶",
        "suggested_price": Decimal("22.00"),
        "product_type": "NORMAL",
        "is_storable": True,
        "skus": [
            {"code": "SKU-BEER-002-330", "name": "330ml单瓶", "spec_text": "330ml", "is_default": True, "suggested_price": Decimal("22.00")},
        ],
    },
    {
        "code": "PRD-SPT-001",
        "name": "芝华士12年",
        "category_code": "CAT-SPIRITS",
        "unit": "瓶",
        "suggested_price": Decimal("680.00"),
        "product_type": "NORMAL",
        "is_storable": True,
        "is_commission_enabled": True,
        "default_commission_type": "RATIO",
        "skus": [
            {"code": "SKU-SPT-001-BTL", "name": "整瓶",   "spec_text": "700ml", "is_default": True,  "suggested_price": Decimal("680.00")},
            {"code": "SKU-SPT-001-CUP", "name": "单杯",   "spec_text": "30ml",  "is_default": False, "suggested_price": Decimal("68.00")},
        ],
    },
    {
        "code": "PRD-FOOD-001",
        "name": "干果拼盘",
        "category_code": "CAT-SNACK",
        "unit": "份",
        "suggested_price": Decimal("58.00"),
        "product_type": "NORMAL",
        "skus": [
            {"code": "SKU-FOOD-001-STD", "name": "标准份", "spec_text": None, "is_default": True, "suggested_price": Decimal("58.00")},
        ],
    },
    {
        "code": "PRD-SVC-001",
        "name": "开瓶服务费",
        "category_code": "CAT-DRINKS",
        "unit": "次",
        "suggested_price": Decimal("30.00"),
        "product_type": "SERVICE",
        "skus": [
            {"code": "SKU-SVC-001-STD", "name": "标准", "spec_text": None, "is_default": True, "suggested_price": Decimal("30.00")},
        ],
    },
]

# 门店售价配置：{sku_code: {store_code: sale_price}}
STORE_SKU_PRICES: dict[str, dict[str, Decimal]] = {
    "SKU-BEER-001-330": {"xinghe": Decimal("20.00"), "jiangnan": Decimal("20.00"), "college": Decimal("18.00")},
    "SKU-BEER-001-500": {"xinghe": Decimal("25.00"), "jiangnan": Decimal("25.00"), "college": Decimal("22.00")},
    "SKU-BEER-002-330": {"xinghe": Decimal("25.00"), "jiangnan": Decimal("25.00"), "college": Decimal("22.00")},
    "SKU-SPT-001-BTL":  {"xinghe": Decimal("750.00"), "jiangnan": Decimal("730.00"), "college": Decimal("700.00")},
    "SKU-SPT-001-CUP":  {"xinghe": Decimal("75.00"),  "jiangnan": Decimal("72.00"),  "college": Decimal("68.00")},
    "SKU-FOOD-001-STD": {"xinghe": Decimal("65.00"), "jiangnan": Decimal("65.00"), "college": Decimal("58.00")},
    "SKU-SVC-001-STD":  {"xinghe": Decimal("30.00"), "jiangnan": Decimal("30.00"), "college": Decimal("30.00")},
}

DEMO_STORE_CODES = ["xinghe", "jiangnan", "college"]


# ---------------------------------------------------------------------------
# 幂等辅助函数
# ---------------------------------------------------------------------------

def _ensure_category(
    session: Session,
    code: str,
    name: str,
    level: int,
    parent_id,
    sort_order: int,
) -> ProductCategory:
    cat = get_product_category_by_code(session=session, code=code)
    if not cat:
        cat = create_product_category(
            session=session,
            body=ProductCategoryCreate(
                code=code,
                name=name,
                level=level,
                parent_id=parent_id,
                sort_order=sort_order,
                is_active=True,
            ),
        )
        logger.info("  创建分类: %s (%s)", name, code)
    return cat


def _ensure_product(session: Session, pdef: dict, category_id) -> Product:
    product = get_product_by_code(session=session, code=pdef["code"])
    if not product:
        extra = {k: pdef[k] for k in ("is_storable", "is_commission_enabled", "default_commission_type") if k in pdef}
        product = create_product(
            session=session,
            body=ProductCreate(
                code=pdef["code"],
                name=pdef["name"],
                category_id=category_id,
                unit=pdef["unit"],
                suggested_price=pdef.get("suggested_price"),
                product_type=pdef.get("product_type", "NORMAL"),
                **extra,
            ),
        )
        logger.info("  创建商品: %s (%s)", pdef["name"], pdef["code"])
    return product


def _ensure_sku(session: Session, sdef: dict, product_id) -> ProductSku:
    sku = get_product_sku_by_code(session=session, code=sdef["code"])
    if not sku:
        sku = create_product_sku(
            session=session,
            body=ProductSkuCreate(
                product_id=product_id,
                code=sdef["code"],
                name=sdef["name"],
                spec_text=sdef.get("spec_text"),
                is_default=sdef.get("is_default", False),
                suggested_price=sdef.get("suggested_price"),
            ),
        )
        logger.info("    创建SKU: %s (%s)", sdef["name"], sdef["code"])
    return sku


def _ensure_store_product(session: Session, store_id, product_id) -> StoreProduct:
    sp = get_store_product(session=session, store_id=store_id, product_id=product_id)
    if not sp:
        sp = create_store_product(
            session=session,
            body=StoreProductCreate(store_id=store_id, product_id=product_id),
        )
    return sp


def _ensure_store_product_sku(
    session: Session, store_id, product_id, sku_id, sale_price: Decimal
) -> StoreProductSku:
    sps = get_store_product_sku(session=session, store_id=store_id, sku_id=sku_id)
    if not sps:
        sps = create_store_product_sku(
            session=session,
            body=StoreProductSkuCreate(
                store_id=store_id,
                product_id=product_id,
                sku_id=sku_id,
                sale_price=sale_price,
            ),
        )
    return sps


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def seed_product_data(session: Session) -> None:
    logger.info("=== 初始化商品分类 ===")
    category_map: dict[str, ProductCategory] = {}
    for cdef in CATEGORY_DEFS:
        parent_id = category_map[cdef["parent_code"]].id if cdef["parent_code"] else None
        cat = _ensure_category(
            session=session,
            code=cdef["code"],
            name=cdef["name"],
            level=cdef["level"],
            parent_id=parent_id,
            sort_order=cdef["sort_order"],
        )
        category_map[cdef["code"]] = cat

    logger.info("=== 初始化商品与SKU ===")
    sku_map: dict[str, ProductSku] = {}
    product_sku_map: dict[str, list[ProductSku]] = {}
    for pdef in PRODUCT_DEFS:
        cat = category_map[pdef["category_code"]]
        product = _ensure_product(session=session, pdef=pdef, category_id=cat.id)
        skus: list[ProductSku] = []
        for sdef in pdef["skus"]:
            sku = _ensure_sku(session=session, sdef=sdef, product_id=product.id)
            sku_map[sdef["code"]] = sku
            skus.append(sku)
        product_sku_map[pdef["code"]] = skus

    logger.info("=== 初始化门店商品与门店SKU ===")
    for store_code in DEMO_STORE_CODES:
        store = get_store_by_code(session=session, code=store_code)
        if not store:
            logger.warning("  门店 %s 不存在，跳过", store_code)
            continue
        logger.info("  门店: %s", store.name)
        for pdef in PRODUCT_DEFS:
            cat = category_map[pdef["category_code"]]
            product = get_product_by_code(session=session, code=pdef["code"])
            assert product is not None
            _ensure_store_product(session=session, store_id=store.id, product_id=product.id)
            for sdef in pdef["skus"]:
                sku = sku_map[sdef["code"]]
                prices = STORE_SKU_PRICES.get(sdef["code"], {})
                sale_price = prices.get(store_code, sdef.get("suggested_price", Decimal("0")))
                _ensure_store_product_sku(
                    session=session,
                    store_id=store.id,
                    product_id=product.id,
                    sku_id=sku.id,
                    sale_price=sale_price,
                )


def main() -> None:
    logger.info("开始初始化商品中心 Demo 数据")
    with Session(engine) as session:
        seed_product_data(session)
    logger.info("商品中心 Demo 数据初始化完成")


if __name__ == "__main__":
    main()
