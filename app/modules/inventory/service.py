import uuid
from decimal import Decimal

from sqlmodel import Session, select

from app.modules.inventory.models import (
    InventoryBalance,
    InventoryTransaction,
    InventoryTransactionCreate,
    TransferOrder,
    TransferOrderCreate,
    Warehouse,
    WarehouseCreate,
)

# ---------------------------------------------------------------------------
# Warehouse
# ---------------------------------------------------------------------------


def list_warehouses(
    *, session: Session, store_id: uuid.UUID | None = None
) -> list[Warehouse]:
    statement = select(Warehouse).order_by(Warehouse.created_at)
    if store_id:
        statement = statement.where(Warehouse.store_id == store_id)
    return list(session.exec(statement).all())


def get_warehouse_by_id(
    *, session: Session, warehouse_id: uuid.UUID
) -> Warehouse | None:
    return session.get(Warehouse, warehouse_id)


def get_warehouse_by_code(
    *, session: Session, store_id: uuid.UUID, code: str
) -> Warehouse | None:
    return session.exec(
        select(Warehouse)
        .where(Warehouse.store_id == store_id)
        .where(Warehouse.code == code)
    ).first()


def create_warehouse(*, session: Session, body: WarehouseCreate) -> Warehouse:
    warehouse = Warehouse.model_validate(body)
    session.add(warehouse)
    session.commit()
    session.refresh(warehouse)
    return warehouse


def update_warehouse(
    *, session: Session, warehouse: Warehouse, data: dict
) -> Warehouse:
    from app.models.base import get_datetime_utc

    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(warehouse, key, value)
    session.add(warehouse)
    session.commit()
    session.refresh(warehouse)
    return warehouse


def delete_warehouse(*, session: Session, warehouse: Warehouse) -> None:
    session.delete(warehouse)
    session.commit()


# ---------------------------------------------------------------------------
# InventoryBalance
# ---------------------------------------------------------------------------


def list_inventory_balances(
    *, session: Session, warehouse_id: uuid.UUID | None = None
) -> list[InventoryBalance]:
    statement = select(InventoryBalance).order_by(InventoryBalance.created_at)
    if warehouse_id:
        statement = statement.where(InventoryBalance.warehouse_id == warehouse_id)
    return list(session.exec(statement).all())


def get_inventory_balance(
    *, session: Session, warehouse_id: uuid.UUID, sku_id: uuid.UUID
) -> InventoryBalance | None:
    return session.exec(
        select(InventoryBalance)
        .where(InventoryBalance.warehouse_id == warehouse_id)
        .where(InventoryBalance.sku_id == sku_id)
    ).first()


def upsert_inventory_balance(
    *,
    session: Session,
    warehouse_id: uuid.UUID,
    sku_id: uuid.UUID,
    delta: Decimal,
    unit: str = "个",
) -> InventoryBalance:
    from app.models.base import get_datetime_utc

    balance = get_inventory_balance(
        session=session, warehouse_id=warehouse_id, sku_id=sku_id
    )
    if balance:
        balance.quantity += delta
        balance.updated_at = get_datetime_utc()
        session.add(balance)
    else:
        balance = InventoryBalance(
            warehouse_id=warehouse_id,
            sku_id=sku_id,
            quantity=delta,
            unit=unit,
        )
        session.add(balance)
    return balance


# ---------------------------------------------------------------------------
# InventoryTransaction
# ---------------------------------------------------------------------------


def list_inventory_transactions(
    *, session: Session, warehouse_id: uuid.UUID | None = None
) -> list[InventoryTransaction]:
    statement = select(InventoryTransaction).order_by(
        InventoryTransaction.created_at.desc()
    )
    if warehouse_id:
        statement = statement.where(InventoryTransaction.warehouse_id == warehouse_id)
    return list(session.exec(statement).all())


def create_inventory_transaction(
    *, session: Session, body: InventoryTransactionCreate
) -> InventoryTransaction:
    tx = InventoryTransaction.model_validate(body)
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx


def record_inventory_change(
    *,
    session: Session,
    warehouse_id: uuid.UUID,
    sku_id: uuid.UUID,
    transaction_type: str,
    quantity: Decimal,
    ref_order_id: uuid.UUID | None = None,
    operator_id: uuid.UUID | None = None,
    remark: str | None = None,
    unit: str = "个",
) -> InventoryTransaction:
    """Record an inventory change and update balance atomically."""
    balance = get_inventory_balance(
        session=session, warehouse_id=warehouse_id, sku_id=sku_id
    )
    quantity_before = balance.quantity if balance else Decimal("0")
    quantity_after = quantity_before + quantity

    upsert_inventory_balance(
        session=session,
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        delta=quantity,
        unit=unit,
    )

    tx = InventoryTransaction(
        warehouse_id=warehouse_id,
        sku_id=sku_id,
        transaction_type=transaction_type,
        quantity=quantity,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        ref_order_id=ref_order_id,
        operator_id=operator_id,
        remark=remark,
    )
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx


# ---------------------------------------------------------------------------
# TransferOrder
# ---------------------------------------------------------------------------


def list_transfer_orders(
    *, session: Session, warehouse_id: uuid.UUID | None = None
) -> list[TransferOrder]:
    statement = select(TransferOrder).order_by(TransferOrder.created_at.desc())
    if warehouse_id:
        statement = statement.where(
            (TransferOrder.from_warehouse_id == warehouse_id)
            | (TransferOrder.to_warehouse_id == warehouse_id)
        )
    return list(session.exec(statement).all())


def get_transfer_order_by_id(
    *, session: Session, transfer_id: uuid.UUID
) -> TransferOrder | None:
    return session.get(TransferOrder, transfer_id)


def get_transfer_order_by_no(
    *, session: Session, transfer_no: str
) -> TransferOrder | None:
    return session.exec(
        select(TransferOrder).where(TransferOrder.transfer_no == transfer_no)
    ).first()


def create_transfer_order(
    *, session: Session, body: TransferOrderCreate
) -> TransferOrder:
    transfer = TransferOrder.model_validate(body)
    session.add(transfer)
    session.commit()
    session.refresh(transfer)
    return transfer


def update_transfer_order(
    *, session: Session, transfer: TransferOrder, data: dict
) -> TransferOrder:
    from app.models.base import get_datetime_utc

    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(transfer, key, value)
    session.add(transfer)
    session.commit()
    session.refresh(transfer)
    return transfer
