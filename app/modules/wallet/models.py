# ruff: noqa: UP037
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import get_datetime_utc

# ---------------------------------------------------------------------------
# Member（会员）
# ---------------------------------------------------------------------------


class MemberBase(SQLModel):
    store_id: uuid.UUID = Field(foreign_key="store.id", description="门店 ID")
    user_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", description="关联用户 ID"
    )
    member_no: str = Field(index=True, unique=True, max_length=64, description="会员编号")
    name: str | None = Field(default=None, max_length=100, description="会员姓名")
    mobile: str | None = Field(default=None, max_length=32, description="手机号")
    status: str = Field(default="ACTIVE", max_length=20, description="会员状态")
    level: str = Field(default="NORMAL", max_length=30, description="会员等级")
    joined_at: datetime | None = Field(default=None, description="入会时间")


class MemberCreate(MemberBase):
    pass


class MemberUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=100, description="会员姓名")
    mobile: str | None = Field(default=None, max_length=32, description="手机号")
    status: str | None = Field(default=None, max_length=20, description="会员状态")
    level: str | None = Field(default=None, max_length=30, description="会员等级")
    joined_at: datetime | None = Field(default=None, description="入会时间")


class Member(MemberBase, table=True):
    __tablename__ = "wallet_member"

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

    principal_account: "PrincipalAccount | None" = Relationship(
        back_populates="member"
    )
    gift_account: "GiftAccount | None" = Relationship(back_populates="member")


class MemberPublic(MemberBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# PrincipalAccount（本金账户）
# ---------------------------------------------------------------------------


class PrincipalAccountBase(SQLModel):
    member_id: uuid.UUID = Field(
        foreign_key="wallet_member.id",
        unique=True,
        description="会员 ID",
    )
    balance: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="本金余额",
    )
    total_recharged: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="累计充值金额",
    )
    total_consumed: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="累计消费金额",
    )
    is_frozen: bool = Field(default=False, description="是否冻结")


class PrincipalAccount(PrincipalAccountBase, table=True):
    __tablename__ = "wallet_principal_account"

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

    member: "Member" = Relationship(back_populates="principal_account")


class PrincipalAccountPublic(PrincipalAccountBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# GiftAccount（赠金账户）
# ---------------------------------------------------------------------------


class GiftAccountBase(SQLModel):
    member_id: uuid.UUID = Field(
        foreign_key="wallet_member.id",
        unique=True,
        description="会员 ID",
    )
    balance: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="赠金余额",
    )
    total_gifted: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="累计赠送金额",
    )
    total_consumed: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="累计消费金额",
    )
    is_frozen: bool = Field(default=False, description="是否冻结")


class GiftAccount(GiftAccountBase, table=True):
    __tablename__ = "wallet_gift_account"

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

    member: "Member" = Relationship(back_populates="gift_account")


class GiftAccountPublic(GiftAccountBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# RechargePlan（充值方案）
# ---------------------------------------------------------------------------


class RechargePlanBase(SQLModel):
    store_id: uuid.UUID = Field(foreign_key="store.id", description="门店 ID")
    name: str = Field(max_length=100, description="充值方案名称")
    recharge_amount: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="充值金额",
    )
    gift_amount: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="赠送金额",
    )
    gift_template_id: uuid.UUID | None = Field(
        default=None, description="关联赠送模板 ID"
    )
    is_active: bool = Field(default=True, description="是否启用")
    description: str | None = Field(default=None, max_length=500, description="说明")


class RechargePlanCreate(RechargePlanBase):
    pass


class RechargePlanUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=100, description="充值方案名称")
    recharge_amount: Decimal | None = Field(default=None, description="充值金额")
    gift_amount: Decimal | None = Field(default=None, description="赠送金额")
    gift_template_id: uuid.UUID | None = Field(
        default=None, description="关联赠送模板 ID"
    )
    is_active: bool | None = Field(default=None, description="是否启用")
    description: str | None = Field(default=None, max_length=500, description="说明")


class RechargePlan(RechargePlanBase, table=True):
    __tablename__ = "wallet_recharge_plan"

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


class RechargePlanPublic(RechargePlanBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# WalletTransaction（钱包流水）
# ---------------------------------------------------------------------------


class WalletTransactionBase(SQLModel):
    member_id: uuid.UUID = Field(foreign_key="wallet_member.id", description="会员 ID")
    account_type: str = Field(
        max_length=20, description="账户类型（PRINCIPAL/GIFT）"
    )
    transaction_type: str = Field(
        max_length=30, description="流水类型（RECHARGE/CONSUME/REFUND/GIFT/ADJUST）"
    )
    amount: Decimal = Field(
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="交易金额（正数入账，负数出账）",
    )
    balance_before: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="交易前余额",
    )
    balance_after: Decimal = Field(
        default=Decimal("0.00"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="交易后余额",
    )
    remark: str | None = Field(default=None, max_length=500, description="备注")
    ref_order_id: uuid.UUID | None = Field(
        default=None, description="关联订单 ID"
    )
    operator_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", description="操作人 ID"
    )


class WalletTransactionCreate(WalletTransactionBase):
    pass


class WalletTransaction(WalletTransactionBase, table=True):
    __tablename__ = "wallet_transaction"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="创建时间",
    )


class WalletTransactionPublic(WalletTransactionBase):
    id: uuid.UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# Recharge request
# ---------------------------------------------------------------------------


class RechargeRequest(SQLModel):
    member_id: uuid.UUID = Field(description="会员 ID")
    recharge_plan_id: uuid.UUID = Field(description="充值方案 ID")
    operator_id: uuid.UUID | None = Field(default=None, description="操作人 ID")
    remark: str | None = Field(default=None, max_length=500, description="备注")
