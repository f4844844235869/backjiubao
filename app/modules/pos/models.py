# ruff: noqa: UP037
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import get_datetime_utc

# ---------------------------------------------------------------------------
# Order（订单）
# ---------------------------------------------------------------------------


class OrderBase(SQLModel):
    store_id: uuid.UUID = Field(foreign_key="store.id", description="门店 ID")
    order_no: str = Field(index=True, unique=True, max_length=64, description="订单编号")
    member_id: uuid.UUID | None = Field(
        default=None, description="会员 ID"
    )
    operator_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", description="操作人 ID"
    )
    status: str = Field(
        default="PENDING", max_length=20, description="订单状态（PENDING/PAID/CANCELLED/REFUNDED）"
    )
    total_amount: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="订单总金额",
    )
    discount_amount: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="优惠金额",
    )
    payable_amount: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="应付金额",
    )
    paid_amount: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="实付金额",
    )
    remark: str | None = Field(default=None, max_length=500, description="备注")


class OrderCreate(OrderBase):
    pass


class OrderUpdate(SQLModel):
    status: str | None = Field(default=None, max_length=20, description="订单状态")
    discount_amount: Decimal | None = Field(default=None, description="优惠金额")
    payable_amount: Decimal | None = Field(default=None, description="应付金额")
    paid_amount: Decimal | None = Field(default=None, description="实付金额")
    remark: str | None = Field(default=None, max_length=500, description="备注")


class Order(OrderBase, table=True):
    __tablename__ = "pos_order"

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

    items: list["OrderItem"] = Relationship(back_populates="order")
    payments: list["Payment"] = Relationship(back_populates="order")


class OrderPublic(OrderBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# OrderItem（订单明细）
# ---------------------------------------------------------------------------


class OrderItemBase(SQLModel):
    order_id: uuid.UUID = Field(foreign_key="pos_order.id", description="订单 ID")
    product_id: uuid.UUID | None = Field(
        default=None, description="商品 ID"
    )
    sku_id: uuid.UUID | None = Field(default=None, description="SKU ID")
    product_name: str = Field(max_length=200, description="商品名称（快照）")
    sku_code: str | None = Field(default=None, max_length=100, description="SKU 编码（快照）")
    unit_price: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="单价",
    )
    quantity: Decimal = Field(
        default=Decimal("1"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="数量",
    )
    subtotal: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="小计金额",
    )
    discount_amount: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="明细优惠金额",
    )


class OrderItemCreate(OrderItemBase):
    pass


class OrderItem(OrderItemBase, table=True):
    __tablename__ = "pos_order_item"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="创建时间",
    )

    order: "Order" = Relationship(back_populates="items")


class OrderItemPublic(OrderItemBase):
    id: uuid.UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# Payment（支付）
# ---------------------------------------------------------------------------


class PaymentBase(SQLModel):
    order_id: uuid.UUID = Field(foreign_key="pos_order.id", description="订单 ID")
    payment_method: str = Field(
        max_length=30,
        description="支付方式（CASH/CARD/WALLET_PRINCIPAL/WALLET_GIFT/WECHAT/ALIPAY）",
    )
    amount: Decimal = Field(
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="支付金额",
    )
    status: str = Field(
        default="SUCCESS", max_length=20, description="支付状态（SUCCESS/FAILED/REFUNDED）"
    )
    remark: str | None = Field(default=None, max_length=500, description="备注")
    operator_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", description="操作人 ID"
    )


class PaymentCreate(PaymentBase):
    pass


class Payment(PaymentBase, table=True):
    __tablename__ = "pos_payment"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="创建时间",
    )

    order: "Order" = Relationship(back_populates="payments")


class PaymentPublic(PaymentBase):
    id: uuid.UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# ShiftHandover（交接班）
# ---------------------------------------------------------------------------


class ShiftHandoverBase(SQLModel):
    store_id: uuid.UUID = Field(foreign_key="store.id", description="门店 ID")
    shift_date: datetime = Field(description="班次日期时间")
    shift_type: str = Field(
        default="MORNING", max_length=20, description="班次类型（MORNING/AFTERNOON/NIGHT）"
    )
    operator_id: uuid.UUID = Field(foreign_key="user.id", description="当班人员 ID")
    handover_to_id: uuid.UUID | None = Field(
        default=None, description="交接人员 ID"
    )
    cash_amount: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="现金金额",
    )
    total_sales: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="本班总销售额",
    )
    order_count: int = Field(default=0, description="本班订单数量")
    status: str = Field(
        default="OPEN", max_length=20, description="班次状态（OPEN/CLOSED）"
    )
    remark: str | None = Field(default=None, max_length=500, description="备注")


class ShiftHandoverCreate(ShiftHandoverBase):
    pass


class ShiftHandoverUpdate(SQLModel):
    handover_to_id: uuid.UUID | None = Field(default=None, description="交接人员 ID")
    cash_amount: Decimal | None = Field(default=None, description="现金金额")
    total_sales: Decimal | None = Field(default=None, description="本班总销售额")
    order_count: int | None = Field(default=None, description="本班订单数量")
    status: str | None = Field(default=None, max_length=20, description="班次状态")
    remark: str | None = Field(default=None, max_length=500, description="备注")


class ShiftHandover(ShiftHandoverBase, table=True):
    __tablename__ = "pos_shift_handover"

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


class ShiftHandoverPublic(ShiftHandoverBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
