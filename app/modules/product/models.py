# ruff: noqa: UP037
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Numeric, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import get_datetime_utc

if TYPE_CHECKING:
    from app.modules.store.models import Store


DISPLAY_TYPE_SELECT = "SELECT"


# ---------------------------------------------------------------------------
# ProductCategory
# ---------------------------------------------------------------------------


class ProductCategoryBase(SQLModel):
    parent_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="product_category.id",
        description="父分类ID，一级分类为空",
    )
    code: str = Field(max_length=64, description="分类编码")
    name: str = Field(max_length=128, description="分类名称")
    level: int = Field(default=1, ge=1, le=2, description="分类层级，1或2")
    sort_order: int = Field(default=0, description="排序值，越小越靠前")
    is_active: bool = Field(default=True, description="是否启用")
    is_deleted: bool = Field(default=False, description="是否逻辑删除")


class ProductCategoryCreate(SQLModel):
    parent_id: uuid.UUID | None = Field(default=None, description="父分类ID")
    code: str = Field(max_length=64, description="分类编码")
    name: str = Field(max_length=128, description="分类名称")
    level: int = Field(default=1, ge=1, le=2, description="分类层级，1或2")
    sort_order: int = Field(default=0, description="排序值")
    is_active: bool = Field(default=True, description="是否启用")


class ProductCategoryUpdate(SQLModel):
    parent_id: uuid.UUID | None = Field(default=None, description="父分类ID")
    code: str | None = Field(default=None, max_length=64, description="分类编码")
    name: str | None = Field(default=None, max_length=128, description="分类名称")
    level: int | None = Field(default=None, ge=1, le=2, description="分类层级")
    sort_order: int | None = Field(default=None, description="排序值")
    is_active: bool | None = Field(default=None, description="是否启用")


class ProductCategory(ProductCategoryBase, table=True):
    __tablename__ = "product_category"
    __table_args__ = (
        UniqueConstraint("code", name="uq_product_category_code"),
        UniqueConstraint("name", "parent_id", name="uq_product_category_name_parent"),
    )

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


class ProductCategoryPublic(ProductCategoryBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------


class ProductBase(SQLModel):
    code: str = Field(max_length=64, description="商品编码")
    name: str = Field(max_length=128, description="商品名称")
    display_name: str | None = Field(
        default=None, max_length=128, description="展示名称"
    )
    print_name: str | None = Field(
        default=None, max_length=64, description="打印名称"
    )
    category_id: uuid.UUID = Field(
        foreign_key="product_category.id", description="分类ID"
    )
    product_type: str = Field(
        default="NORMAL", max_length=32, description="商品类型"
    )
    brand_name: str | None = Field(
        default=None, max_length=128, description="品牌名称"
    )
    series_name: str | None = Field(
        default=None, max_length=128, description="系列名称"
    )
    description: str | None = Field(default=None, description="商品描述")
    unit: str = Field(default="个", max_length=32, description="默认销售单位")
    suggested_price: Decimal | None = Field(
        default=None,
        sa_type=Numeric(18, 2),  # type: ignore
        description="建议零售价",
    )
    default_fund_usage_type: str = Field(
        default="ALL_ALLOWED", max_length=32, description="默认资金限制"
    )
    is_inventory_item: bool = Field(default=False, description="是否参与库存")
    is_commission_enabled: bool = Field(default=False, description="是否参与业绩")
    default_commission_type: str = Field(
        default="NONE", max_length=16, description="默认业绩类型"
    )
    default_commission_value: Decimal = Field(
        default=Decimal("0"),
        sa_type=Numeric(18, 2),  # type: ignore
        description="默认业绩值",
    )
    is_profit_enabled: bool = Field(default=False, description="是否参与利润分析")
    standard_cost_price: Decimal | None = Field(
        default=None,
        sa_type=Numeric(18, 2),  # type: ignore
        description="标准成本价（参考）",
    )
    is_storable: bool = Field(default=False, description="是否允许存酒")
    is_gift_allowed: bool = Field(default=False, description="是否允许赠送")
    is_min_consumption_eligible: bool = Field(
        default=True, description="是否计入低消"
    )
    is_front_visible: bool = Field(default=True, description="是否前台可见")
    is_pos_visible: bool = Field(default=True, description="是否POS可见")
    is_sale_enabled: bool = Field(default=True, description="是否允许销售")
    is_active: bool = Field(default=True, description="是否启用")
    is_deleted: bool = Field(default=False, description="是否逻辑删除")
    remark: str | None = Field(default=None, max_length=512, description="备注")


class ProductCreate(SQLModel):
    code: str = Field(max_length=64, description="商品编码")
    name: str = Field(max_length=128, description="商品名称")
    display_name: str | None = Field(default=None, max_length=128)
    print_name: str | None = Field(default=None, max_length=64)
    category_id: uuid.UUID
    product_type: str = Field(default="NORMAL", max_length=32)
    brand_name: str | None = Field(default=None, max_length=128)
    series_name: str | None = Field(default=None, max_length=128)
    description: str | None = Field(default=None)
    unit: str = Field(default="个", max_length=32)
    suggested_price: Decimal | None = Field(default=None)
    default_fund_usage_type: str = Field(default="ALL_ALLOWED", max_length=32)
    is_inventory_item: bool = Field(default=False)
    is_commission_enabled: bool = Field(default=False)
    default_commission_type: str = Field(default="NONE", max_length=16)
    default_commission_value: Decimal = Field(default=Decimal("0"))
    is_profit_enabled: bool = Field(default=False)
    standard_cost_price: Decimal | None = Field(default=None)
    is_storable: bool = Field(default=False)
    is_gift_allowed: bool = Field(default=False)
    is_min_consumption_eligible: bool = Field(default=True)
    is_front_visible: bool = Field(default=True)
    is_pos_visible: bool = Field(default=True)
    is_sale_enabled: bool = Field(default=True)
    is_active: bool = Field(default=True)
    remark: str | None = Field(default=None, max_length=512)


class ProductUpdate(SQLModel):
    code: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=128)
    display_name: str | None = Field(default=None, max_length=128)
    print_name: str | None = Field(default=None, max_length=64)
    category_id: uuid.UUID | None = Field(default=None)
    product_type: str | None = Field(default=None, max_length=32)
    brand_name: str | None = Field(default=None, max_length=128)
    series_name: str | None = Field(default=None, max_length=128)
    description: str | None = Field(default=None)
    unit: str | None = Field(default=None, max_length=32)
    suggested_price: Decimal | None = Field(default=None)
    default_fund_usage_type: str | None = Field(default=None, max_length=32)
    is_inventory_item: bool | None = Field(default=None)
    is_commission_enabled: bool | None = Field(default=None)
    default_commission_type: str | None = Field(default=None, max_length=16)
    default_commission_value: Decimal | None = Field(default=None)
    is_profit_enabled: bool | None = Field(default=None)
    standard_cost_price: Decimal | None = Field(default=None)
    is_storable: bool | None = Field(default=None)
    is_gift_allowed: bool | None = Field(default=None)
    is_min_consumption_eligible: bool | None = Field(default=None)
    is_front_visible: bool | None = Field(default=None)
    is_pos_visible: bool | None = Field(default=None)
    is_sale_enabled: bool | None = Field(default=None)
    is_active: bool | None = Field(default=None)
    remark: str | None = Field(default=None, max_length=512)


class Product(ProductBase, table=True):
    __tablename__ = "product"
    __table_args__ = (
        UniqueConstraint("code", name="uq_product_code"),
        UniqueConstraint("name", name="uq_product_name"),
    )

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

    category: Optional["ProductCategory"] = Relationship(back_populates="products")
    skus: list["ProductSku"] = Relationship(back_populates="product")
    store_products: list["StoreProduct"] = Relationship(back_populates="product")
    store_product_skus: list["StoreProductSku"] = Relationship(
        back_populates="product"
    )
    attribute_assignments: list["ProductAttributeAssignment"] = Relationship(
        back_populates="product"
    )


class ProductPublic(ProductBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# ProductAttribute
# ---------------------------------------------------------------------------


class ProductAttributeBase(SQLModel):
    code: str = Field(max_length=64, description="属性编码")
    name: str = Field(max_length=128, description="属性名称")
    display_type: str = Field(
        default=DISPLAY_TYPE_SELECT,
        max_length=32,
        description="展示类型，仅支持 SELECT",
    )
    sort_order: int = Field(default=0, description="排序")
    is_active: bool = Field(default=True, description="是否启用")


class ProductAttributeCreate(ProductAttributeBase):
    pass


class ProductAttributeUpdate(SQLModel):
    code: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=128)
    display_type: str | None = Field(default=None, max_length=32)
    sort_order: int | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class ProductAttribute(ProductAttributeBase, table=True):
    __tablename__ = "product_attribute"
    __table_args__ = (UniqueConstraint("code", name="uq_prod_attr_code"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    values: list["ProductAttributeValue"] = Relationship(back_populates="attribute")
    assignments: list["ProductAttributeAssignment"] = Relationship(
        back_populates="attribute"
    )
    sku_attribute_values: list["ProductSkuAttributeValue"] = Relationship(
        back_populates="attribute"
    )


class ProductAttributePublic(ProductAttributeBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ProductAttributeValueBase(SQLModel):
    attribute_id: uuid.UUID = Field(
        foreign_key="product_attribute.id",
        description="属性ID",
    )
    code: str = Field(max_length=64, description="属性值编码")
    name: str = Field(max_length=128, description="属性值名称")
    sort_order: int = Field(default=0, description="排序")
    is_active: bool = Field(default=True, description="是否启用")


class ProductAttributeValueCreate(SQLModel):
    attribute_id: uuid.UUID
    code: str = Field(max_length=64)
    name: str = Field(max_length=128)
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)


class ProductAttributeValueUpdate(SQLModel):
    code: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=128)
    sort_order: int | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class ProductAttributeValue(ProductAttributeValueBase, table=True):
    __tablename__ = "product_attribute_value"
    __table_args__ = (
        UniqueConstraint(
            "attribute_id",
            "code",
            name="uq_prod_attr_val_attr_code",
        ),
        UniqueConstraint(
            "attribute_id",
            "name",
            name="uq_prod_attr_val_attr_name",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    attribute: Optional["ProductAttribute"] = Relationship(back_populates="values")
    assignment_values: list["ProductAttributeAssignmentValue"] = Relationship(
        back_populates="attribute_value"
    )
    sku_attribute_values: list["ProductSkuAttributeValue"] = Relationship(
        back_populates="attribute_value"
    )


class ProductAttributeValuePublic(ProductAttributeValueBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ProductAttributeAssignmentBase(SQLModel):
    product_id: uuid.UUID = Field(foreign_key="product.id", description="商品ID")
    attribute_id: uuid.UUID = Field(
        foreign_key="product_attribute.id",
        description="属性ID",
    )
    sort_order: int = Field(default=0, description="排序")
    is_required: bool = Field(default=True, description="是否必选")


class ProductAttributeAssignmentCreate(SQLModel):
    product_id: uuid.UUID
    attribute_id: uuid.UUID
    sort_order: int = Field(default=0)
    is_required: bool = Field(default=True)


class ProductAttributeAssignmentUpdate(SQLModel):
    sort_order: int | None = Field(default=None)
    is_required: bool | None = Field(default=None)


class ProductAttributeAssignment(ProductAttributeAssignmentBase, table=True):
    __tablename__ = "product_attribute_assignment"
    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "attribute_id",
            name="uq_prod_attr_asg_prod_attr",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    product: Optional["Product"] = Relationship(back_populates="attribute_assignments")
    attribute: Optional["ProductAttribute"] = Relationship(back_populates="assignments")
    values: list["ProductAttributeAssignmentValue"] = Relationship(
        back_populates="assignment"
    )


class ProductAttributeAssignmentValueBase(SQLModel):
    assignment_id: uuid.UUID = Field(
        foreign_key="product_attribute_assignment.id",
        description="商品属性绑定ID",
    )
    attribute_value_id: uuid.UUID = Field(
        foreign_key="product_attribute_value.id",
        description="属性值ID",
    )
    sort_order: int = Field(default=0, description="排序")
    is_default: bool = Field(default=False, description="是否默认值")


class ProductAttributeAssignmentValueCreate(SQLModel):
    assignment_id: uuid.UUID
    attribute_value_id: uuid.UUID
    sort_order: int = Field(default=0)
    is_default: bool = Field(default=False)


class ProductAttributeAssignmentValue(ProductAttributeAssignmentValueBase, table=True):
    __tablename__ = "product_attribute_assignment_value"
    __table_args__ = (
        UniqueConstraint(
            "assignment_id",
            "attribute_value_id",
            name="uq_prod_attr_asg_val_asg_val",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    assignment: Optional["ProductAttributeAssignment"] = Relationship(
        back_populates="values"
    )
    attribute_value: Optional["ProductAttributeValue"] = Relationship(
        back_populates="assignment_values"
    )


class ProductAttributeAssignmentValuePublic(ProductAttributeAssignmentValueBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    attribute_value: ProductAttributeValuePublic


class ProductAttributeAssignmentPublic(ProductAttributeAssignmentBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    attribute: ProductAttributePublic
    values: list[ProductAttributeAssignmentValuePublic] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# ProductSku
# ---------------------------------------------------------------------------


class ProductSkuBase(SQLModel):
    product_id: uuid.UUID = Field(foreign_key="product.id", description="商品ID")
    code: str = Field(max_length=64, description="SKU编码")
    name: str = Field(max_length=128, description="SKU名称")
    spec_text: str | None = Field(
        default=None, max_length=256, description="规格描述"
    )
    suggested_price: Decimal | None = Field(
        default=None,
        sa_type=Numeric(18, 2),  # type: ignore
        description="SKU建议价",
    )
    barcode: str | None = Field(default=None, max_length=64, description="条码")
    is_default: bool = Field(default=False, description="是否默认SKU")
    fund_usage_type: str | None = Field(
        default=None, max_length=32, description="SKU级资金限制，空则继承商品"
    )
    is_inventory_item: bool | None = Field(
        default=None, description="SKU是否参与库存，空则继承商品"
    )
    is_commission_enabled: bool | None = Field(
        default=None, description="SKU是否参与业绩，空则继承商品"
    )
    commission_type: str | None = Field(
        default=None, max_length=16, description="SKU级业绩类型，空则继承商品"
    )
    commission_value: Decimal | None = Field(
        default=None,
        sa_type=Numeric(18, 2),  # type: ignore
        description="SKU级业绩值",
    )
    is_profit_enabled: bool | None = Field(
        default=None, description="SKU是否参与利润分析"
    )
    standard_cost_price: Decimal | None = Field(
        default=None,
        sa_type=Numeric(18, 2),  # type: ignore
        description="SKU标准成本价",
    )
    inventory_mode: str = Field(
        default="NONE", max_length=16, description="库存模式"
    )
    allow_negative_inventory: bool = Field(
        default=False, description="是否允许负库存"
    )
    is_sale_enabled: bool = Field(default=True, description="是否允许销售")
    is_active: bool = Field(default=True, description="是否启用")
    is_deleted: bool = Field(default=False, description="是否逻辑删除")


class ProductSkuCreate(SQLModel):
    product_id: uuid.UUID
    code: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=128)
    spec_text: str | None = Field(default=None, max_length=256)
    suggested_price: Decimal | None = Field(default=None)
    barcode: str | None = Field(default=None, max_length=64)
    is_default: bool = Field(default=False)
    fund_usage_type: str | None = Field(default=None, max_length=32)
    is_inventory_item: bool | None = Field(default=None)
    is_commission_enabled: bool | None = Field(default=None)
    commission_type: str | None = Field(default=None, max_length=16)
    commission_value: Decimal | None = Field(default=None)
    is_profit_enabled: bool | None = Field(default=None)
    standard_cost_price: Decimal | None = Field(default=None)
    inventory_mode: str = Field(default="NONE", max_length=16)
    allow_negative_inventory: bool = Field(default=False)
    is_sale_enabled: bool = Field(default=True)
    is_active: bool = Field(default=True)


class ProductSkuUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=128)
    spec_text: str | None = Field(default=None, max_length=256)
    suggested_price: Decimal | None = Field(default=None)
    barcode: str | None = Field(default=None, max_length=64)
    is_default: bool | None = Field(default=None)
    fund_usage_type: str | None = Field(default=None, max_length=32)
    is_inventory_item: bool | None = Field(default=None)
    is_commission_enabled: bool | None = Field(default=None)
    commission_type: str | None = Field(default=None, max_length=16)
    commission_value: Decimal | None = Field(default=None)
    is_profit_enabled: bool | None = Field(default=None)
    standard_cost_price: Decimal | None = Field(default=None)
    inventory_mode: str | None = Field(default=None, max_length=16)
    allow_negative_inventory: bool | None = Field(default=None)
    is_sale_enabled: bool | None = Field(default=None)
    is_active: bool | None = Field(default=None)
    code: str | None = Field(default=None, max_length=64)


class ProductSku(ProductSkuBase, table=True):
    __tablename__ = "product_sku"
    __table_args__ = (
        UniqueConstraint("code", name="uq_product_sku_code"),
        UniqueConstraint(
            "product_id", "name", name="uq_product_sku_product_id_name"
        ),
    )

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

    product: Optional["Product"] = Relationship(back_populates="skus")
    store_product_skus: list["StoreProductSku"] = Relationship(
        back_populates="sku"
    )
    inventory_mappings: list["SkuInventoryMapping"] = Relationship(
        back_populates="sku",
        sa_relationship_kwargs={"foreign_keys": "[SkuInventoryMapping.sku_id]"},
    )
    attribute_values: list["ProductSkuAttributeValue"] = Relationship(
        back_populates="sku"
    )


class ProductSkuAttributeValueBase(SQLModel):
    sku_id: uuid.UUID = Field(foreign_key="product_sku.id", description="SKU ID")
    attribute_id: uuid.UUID = Field(
        foreign_key="product_attribute.id", description="属性ID"
    )
    attribute_value_id: uuid.UUID = Field(
        foreign_key="product_attribute_value.id",
        description="属性值ID",
    )


class ProductSkuAttributeValue(ProductSkuAttributeValueBase, table=True):
    __tablename__ = "product_sku_attribute_value"
    __table_args__ = (
        UniqueConstraint(
            "sku_id",
            "attribute_id",
            name="uq_prod_sku_attr_val_sku_attr",
        ),
        UniqueConstraint(
            "sku_id",
            "attribute_value_id",
            name="uq_prod_sku_attr_val_sku_val",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    sku: Optional["ProductSku"] = Relationship(back_populates="attribute_values")
    attribute: Optional["ProductAttribute"] = Relationship(
        back_populates="sku_attribute_values"
    )
    attribute_value: Optional["ProductAttributeValue"] = Relationship(
        back_populates="sku_attribute_values"
    )


class ProductSkuAttributeValuePublic(SQLModel):
    attribute_id: uuid.UUID
    attribute_code: str
    attribute_name: str
    attribute_value_id: uuid.UUID
    attribute_value_code: str
    attribute_value_name: str


class ProductSkuPublic(ProductSkuBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    attribute_values: list[ProductSkuAttributeValuePublic] = Field(default_factory=list)


class ProductSkuGenerationSummary(SQLModel):
    created: list[ProductSkuPublic] = Field(default_factory=list)
    retained: list[ProductSkuPublic] = Field(default_factory=list)
    deactivated: list[ProductSkuPublic] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# StoreProduct
# ---------------------------------------------------------------------------


class StoreProductBase(SQLModel):
    store_id: uuid.UUID = Field(foreign_key="store.id", description="门店ID")
    product_id: uuid.UUID = Field(foreign_key="product.id", description="商品ID")
    is_enabled: bool = Field(default=True, description="门店内是否启用该商品")
    is_visible: bool = Field(default=True, description="门店前台是否可见")
    sort_order: int = Field(default=0, description="门店内排序")


class StoreProductCreate(SQLModel):
    store_id: uuid.UUID
    product_id: uuid.UUID
    is_enabled: bool = Field(default=True)
    is_visible: bool = Field(default=True)
    sort_order: int = Field(default=0)


class StoreProductUpdate(SQLModel):
    is_enabled: bool | None = Field(default=None)
    is_visible: bool | None = Field(default=None)
    sort_order: int | None = Field(default=None)


class StoreProduct(StoreProductBase, table=True):
    __tablename__ = "store_product"
    __table_args__ = (
        UniqueConstraint(
            "store_id", "product_id", name="uq_store_product_store_id_product_id"
        ),
    )

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

    store: Optional["Store"] = Relationship(back_populates="store_products")
    product: Optional["Product"] = Relationship(back_populates="store_products")


class StoreProductPublic(StoreProductBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# StoreProductSku
# ---------------------------------------------------------------------------


class StoreProductSkuBase(SQLModel):
    store_id: uuid.UUID = Field(foreign_key="store.id", description="门店ID")
    product_id: uuid.UUID = Field(foreign_key="product.id", description="商品ID")
    sku_id: uuid.UUID = Field(foreign_key="product_sku.id", description="SKU ID")
    sale_price: Decimal = Field(
        default=Decimal("0"),
        sa_type=Numeric(18, 2),  # type: ignore
        description="门店实际售价",
    )
    list_price: Decimal | None = Field(
        default=None,
        sa_type=Numeric(18, 2),  # type: ignore
        description="门店划线价/参考价",
    )
    fund_usage_type: str | None = Field(
        default=None, max_length=32, description="门店SKU级资金限制，空则继承"
    )
    is_sale_enabled: bool = Field(default=True, description="门店内SKU是否可销售")
    is_visible: bool = Field(default=True, description="门店内SKU是否可见")
    is_default: bool = Field(default=False, description="是否门店默认销售SKU")
    effective_from: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="生效开始时间",
    )
    effective_to: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="生效结束时间",
    )


class StoreProductSkuCreate(SQLModel):
    store_id: uuid.UUID
    product_id: uuid.UUID
    sku_id: uuid.UUID
    sale_price: Decimal = Field(default=Decimal("0"))
    list_price: Decimal | None = Field(default=None)
    fund_usage_type: str | None = Field(default=None, max_length=32)
    is_sale_enabled: bool = Field(default=True)
    is_visible: bool = Field(default=True)
    is_default: bool = Field(default=False)
    effective_from: datetime | None = Field(default=None)
    effective_to: datetime | None = Field(default=None)


class StoreProductSkuUpdate(SQLModel):
    sale_price: Decimal | None = Field(default=None)
    list_price: Decimal | None = Field(default=None)
    fund_usage_type: str | None = Field(default=None, max_length=32)
    is_sale_enabled: bool | None = Field(default=None)
    is_visible: bool | None = Field(default=None)
    is_default: bool | None = Field(default=None)
    effective_from: datetime | None = Field(default=None)
    effective_to: datetime | None = Field(default=None)


class StoreProductSku(StoreProductSkuBase, table=True):
    __tablename__ = "store_product_sku"
    __table_args__ = (
        UniqueConstraint(
            "store_id", "sku_id", name="uq_store_product_sku_store_id_sku_id"
        ),
    )

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

    store: Optional["Store"] = Relationship(back_populates="store_product_skus")
    product: Optional["Product"] = Relationship(back_populates="store_product_skus")
    sku: Optional["ProductSku"] = Relationship(back_populates="store_product_skus")


class StoreProductSkuPublic(StoreProductSkuBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# SkuInventoryMapping
# ---------------------------------------------------------------------------


class SkuInventoryMappingBase(SQLModel):
    sku_id: uuid.UUID = Field(foreign_key="product_sku.id", description="销售SKU ID")
    inventory_product_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="product.id",
        description="对应库存商品ID",
    )
    inventory_sku_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="product_sku.id",
        description="对应库存SKU ID",
    )
    deduct_quantity: Decimal = Field(
        default=Decimal("1"),
        sa_type=Numeric(18, 4),  # type: ignore
        description="扣减数量",
    )
    deduct_unit: str = Field(default="个", max_length=32, description="扣减单位")
    sort_order: int = Field(default=0, description="顺序")


class SkuInventoryMappingCreate(SQLModel):
    sku_id: uuid.UUID
    inventory_product_id: uuid.UUID | None = Field(default=None)
    inventory_sku_id: uuid.UUID | None = Field(default=None)
    deduct_quantity: Decimal = Field(default=Decimal("1"))
    deduct_unit: str = Field(default="个", max_length=32)
    sort_order: int = Field(default=0)


class SkuInventoryMappingUpdate(SQLModel):
    inventory_product_id: uuid.UUID | None = Field(default=None)
    inventory_sku_id: uuid.UUID | None = Field(default=None)
    deduct_quantity: Decimal | None = Field(default=None)
    deduct_unit: str | None = Field(default=None, max_length=32)
    sort_order: int | None = Field(default=None)


class SkuInventoryMapping(SkuInventoryMappingBase, table=True):
    __tablename__ = "sku_inventory_mapping"

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

    sku: Optional["ProductSku"] = Relationship(
        back_populates="inventory_mappings",
        sa_relationship_kwargs={"foreign_keys": "[SkuInventoryMapping.sku_id]"},
    )


class SkuInventoryMappingPublic(SkuInventoryMappingBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
