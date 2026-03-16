# ruff: noqa: UP037
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Numeric
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import get_datetime_utc

# ---------------------------------------------------------------------------
# Category（商品分类）
# ---------------------------------------------------------------------------


class CategoryBase(SQLModel):
    store_id: uuid.UUID = Field(foreign_key="store.id", description="门店 ID")
    parent_id: uuid.UUID | None = Field(default=None, description="父分类 ID")
    name: str = Field(max_length=100, description="分类名称")
    sort_order: int = Field(default=0, description="排序值")
    is_active: bool = Field(default=True, description="是否启用")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(SQLModel):
    parent_id: uuid.UUID | None = Field(default=None, description="父分类 ID")
    name: str | None = Field(default=None, max_length=100, description="分类名称")
    sort_order: int | None = Field(default=None, description="排序值")
    is_active: bool | None = Field(default=None, description="是否启用")


class Category(CategoryBase, table=True):
    __tablename__ = "product_category"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="创建时间",
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="更新时间",
    )

    products: list["Product"] = Relationship(back_populates="category")


class CategoryPublic(CategoryBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Product（商品）
# ---------------------------------------------------------------------------

PRICE_DISPLAY_MODE_NET = "NET_PROFIT"
PRICE_DISPLAY_MODE_GROSS = "GROSS_PROFIT"
PRICE_DISPLAY_MODE_BOTH = "BOTH"


class ProductBase(SQLModel):
    store_id: uuid.UUID = Field(foreign_key="store.id", description="门店 ID")
    category_id: uuid.UUID | None = Field(
        default=None, foreign_key="product_category.id", description="分类 ID"
    )
    code: str = Field(index=True, max_length=100, description="商品编码")
    name: str = Field(max_length=200, description="商品名称")
    unit: str = Field(default="个", max_length=30, description="计量单位")
    status: str = Field(default="ACTIVE", max_length=20, description="商品状态")
    # 价格与利润字段
    selling_price: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="销售价格",
    )
    cost_price: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="成本价格",
    )
    # 毛利润 = selling_price - cost_price
    # 净利润字段（可单独配置，也可自动计算）
    net_profit_price: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="净利润参考价格",
    )
    # 可配置显示模式：NET_PROFIT | GROSS_PROFIT | BOTH
    price_display_mode: str = Field(
        default=PRICE_DISPLAY_MODE_GROSS,
        max_length=20,
        description="价格显示模式（NET_PROFIT/GROSS_PROFIT/BOTH）",
    )
    description: str | None = Field(default=None, max_length=1000, description="商品描述")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(SQLModel):
    category_id: uuid.UUID | None = Field(default=None, description="分类 ID")
    code: str | None = Field(default=None, max_length=100, description="商品编码")
    name: str | None = Field(default=None, max_length=200, description="商品名称")
    unit: str | None = Field(default=None, max_length=30, description="计量单位")
    status: str | None = Field(default=None, max_length=20, description="商品状态")
    selling_price: Decimal | None = Field(default=None, description="销售价格")
    cost_price: Decimal | None = Field(default=None, description="成本价格")
    net_profit_price: Decimal | None = Field(default=None, description="净利润参考价格")
    price_display_mode: str | None = Field(
        default=None,
        max_length=20,
        description="价格显示模式（NET_PROFIT/GROSS_PROFIT/BOTH）",
    )
    description: str | None = Field(default=None, max_length=1000, description="商品描述")


class Product(ProductBase, table=True):
    __tablename__ = "product"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="创建时间",
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="更新时间",
    )

    category: Optional["Category"] = Relationship(back_populates="products")
    skus: list["SKU"] = Relationship(back_populates="product")


class ProductPublic(ProductBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# SKU
# ---------------------------------------------------------------------------


class SKUBase(SQLModel):
    product_id: uuid.UUID = Field(foreign_key="product.id", description="商品 ID")
    sku_code: str = Field(index=True, max_length=100, description="SKU 编码")
    spec_name: str | None = Field(default=None, max_length=200, description="规格名称")
    barcode: str | None = Field(default=None, max_length=100, description="条形码")
    price: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="SKU 销售价格",
    )
    cost_price: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="SKU 成本价格",
    )
    net_profit_price: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="SKU 净利润参考价格",
    )
    price_display_mode: str = Field(
        default=PRICE_DISPLAY_MODE_GROSS,
        max_length=20,
        description="价格显示模式（NET_PROFIT/GROSS_PROFIT/BOTH）",
    )
    is_active: bool = Field(default=True, description="是否启用")


class SKUCreate(SKUBase):
    pass


class SKUUpdate(SQLModel):
    sku_code: str | None = Field(default=None, max_length=100, description="SKU 编码")
    spec_name: str | None = Field(default=None, max_length=200, description="规格名称")
    barcode: str | None = Field(default=None, max_length=100, description="条形码")
    price: Decimal | None = Field(default=None, description="SKU 销售价格")
    cost_price: Decimal | None = Field(default=None, description="SKU 成本价格")
    net_profit_price: Decimal | None = Field(default=None, description="SKU 净利润参考价格")
    price_display_mode: str | None = Field(
        default=None,
        max_length=20,
        description="价格显示模式（NET_PROFIT/GROSS_PROFIT/BOTH）",
    )
    is_active: bool | None = Field(default=None, description="是否启用")


class SKU(SKUBase, table=True):
    __tablename__ = "product_sku"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="创建时间",
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="更新时间",
    )

    product: "Product" = Relationship(back_populates="skus")


class SKUPublic(SKUBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# FundLimit（资金限制）
# ---------------------------------------------------------------------------


class FundLimitBase(SQLModel):
    store_id: uuid.UUID = Field(foreign_key="store.id", description="门店 ID")
    name: str = Field(max_length=100, description="限制名称")
    limit_type: str = Field(max_length=30, description="限制类型（如 DAILY/SINGLE）")
    amount: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="限制金额",
    )
    is_active: bool = Field(default=True, description="是否启用")
    description: str | None = Field(default=None, max_length=500, description="说明")


class FundLimitCreate(FundLimitBase):
    pass


class FundLimitUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=100, description="限制名称")
    limit_type: str | None = Field(default=None, max_length=30, description="限制类型")
    amount: Decimal | None = Field(default=None, description="限制金额")
    is_active: bool | None = Field(default=None, description="是否启用")
    description: str | None = Field(default=None, max_length=500, description="说明")


class FundLimit(FundLimitBase, table=True):
    __tablename__ = "product_fund_limit"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="创建时间",
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="更新时间",
    )


class FundLimitPublic(FundLimitBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# GiftTemplate（赠送模板）
# ---------------------------------------------------------------------------


class GiftTemplateBase(SQLModel):
    store_id: uuid.UUID = Field(foreign_key="store.id", description="门店 ID")
    name: str = Field(max_length=100, description="赠送模板名称")
    gift_type: str = Field(
        default="AMOUNT", max_length=30, description="赠送类型（AMOUNT/PRODUCT）"
    )
    gift_amount: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="赠送金额",
    )
    is_active: bool = Field(default=True, description="是否启用")
    description: str | None = Field(default=None, max_length=500, description="说明")


class GiftTemplateCreate(GiftTemplateBase):
    pass


class GiftTemplateUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=100, description="赠送模板名称")
    gift_type: str | None = Field(default=None, max_length=30, description="赠送类型")
    gift_amount: Decimal | None = Field(default=None, description="赠送金额")
    is_active: bool | None = Field(default=None, description="是否启用")
    description: str | None = Field(default=None, max_length=500, description="说明")


class GiftTemplate(GiftTemplateBase, table=True):
    __tablename__ = "product_gift_template"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="创建时间",
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="更新时间",
    )


class GiftTemplatePublic(GiftTemplateBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
