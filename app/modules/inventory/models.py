# ruff: noqa: UP037
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import get_datetime_utc

# ---------------------------------------------------------------------------
# Warehouse（仓库）
# ---------------------------------------------------------------------------


class WarehouseBase(SQLModel):
    store_id: uuid.UUID = Field(foreign_key="store.id", description="门店 ID")
    code: str = Field(index=True, max_length=100, description="仓库编码")
    name: str = Field(max_length=100, description="仓库名称")
    warehouse_type: str = Field(
        default="MAIN", max_length=30, description="仓库类型（MAIN/TRANSIT/RETURNED）"
    )
    is_active: bool = Field(default=True, description="是否启用")
    address: str | None = Field(default=None, max_length=500, description="仓库地址")
    remark: str | None = Field(default=None, max_length=500, description="备注")


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(SQLModel):
    code: str | None = Field(default=None, max_length=100, description="仓库编码")
    name: str | None = Field(default=None, max_length=100, description="仓库名称")
    warehouse_type: str | None = Field(default=None, max_length=30, description="仓库类型")
    is_active: bool | None = Field(default=None, description="是否启用")
    address: str | None = Field(default=None, max_length=500, description="仓库地址")
    remark: str | None = Field(default=None, max_length=500, description="备注")


class Warehouse(WarehouseBase, table=True):
    __tablename__ = "inventory_warehouse"

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

    balances: list["InventoryBalance"] = Relationship(back_populates="warehouse")
    transactions: list["InventoryTransaction"] = Relationship(
        back_populates="warehouse"
    )


class WarehousePublic(WarehouseBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# InventoryBalance（库存余额）
# ---------------------------------------------------------------------------


class InventoryBalanceBase(SQLModel):
    warehouse_id: uuid.UUID = Field(
        foreign_key="inventory_warehouse.id", description="仓库 ID"
    )
    sku_id: uuid.UUID = Field(description="SKU ID")
    quantity: Decimal = Field(
        default=Decimal("0"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="当前库存数量",
    )
    unit: str = Field(default="个", max_length=30, description="计量单位")
    min_quantity: Decimal = Field(
        default=Decimal("0"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="最低库存预警值",
    )


class InventoryBalance(InventoryBalanceBase, table=True):
    __tablename__ = "inventory_balance"

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

    warehouse: "Warehouse" = Relationship(back_populates="balances")


class InventoryBalancePublic(InventoryBalanceBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# InventoryTransaction（库存流水）
# ---------------------------------------------------------------------------


class InventoryTransactionBase(SQLModel):
    warehouse_id: uuid.UUID = Field(
        foreign_key="inventory_warehouse.id", description="仓库 ID"
    )
    sku_id: uuid.UUID = Field(description="SKU ID")
    transaction_type: str = Field(
        max_length=30,
        description="流水类型（IN/OUT/ADJUST/TRANSFER_IN/TRANSFER_OUT）",
    )
    quantity: Decimal = Field(
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="变动数量（正数入库，负数出库）",
    )
    quantity_before: Decimal = Field(
        default=Decimal("0"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="变动前数量",
    )
    quantity_after: Decimal = Field(
        default=Decimal("0"),
        sa_type=Numeric(precision=18, scale=4),  # type: ignore
        description="变动后数量",
    )
    ref_order_id: uuid.UUID | None = Field(
        default=None, description="关联单据 ID（调拨单/订单等）"
    )
    operator_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", description="操作人 ID"
    )
    remark: str | None = Field(default=None, max_length=500, description="备注")


class InventoryTransactionCreate(InventoryTransactionBase):
    pass


class InventoryTransaction(InventoryTransactionBase, table=True):
    __tablename__ = "inventory_transaction"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="创建时间",
    )

    warehouse: "Warehouse" = Relationship(back_populates="transactions")


class InventoryTransactionPublic(InventoryTransactionBase):
    id: uuid.UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# TransferOrder（调拨单）
# ---------------------------------------------------------------------------


class TransferOrderBase(SQLModel):
    from_warehouse_id: uuid.UUID = Field(
        foreign_key="inventory_warehouse.id", description="调出仓库 ID"
    )
    to_warehouse_id: uuid.UUID = Field(
        foreign_key="inventory_warehouse.id", description="调入仓库 ID"
    )
    transfer_no: str = Field(
        index=True, unique=True, max_length=64, description="调拨单编号"
    )
    status: str = Field(
        default="DRAFT", max_length=20, description="状态（DRAFT/CONFIRMED/COMPLETED/CANCELLED）"
    )
    operator_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", description="操作人 ID"
    )
    remark: str | None = Field(default=None, max_length=500, description="备注")


class TransferOrderCreate(TransferOrderBase):
    pass


class TransferOrderUpdate(SQLModel):
    status: str | None = Field(default=None, max_length=20, description="状态")
    remark: str | None = Field(default=None, max_length=500, description="备注")


class TransferOrder(TransferOrderBase, table=True):
    __tablename__ = "inventory_transfer_order"

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


class TransferOrderPublic(TransferOrderBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
