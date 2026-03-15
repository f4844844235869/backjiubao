"""Tests for Inventory (库存) module."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.modules.inventory.models import (
    TransferOrderCreate,
    WarehouseCreate,
)
from app.modules.inventory.service import (
    create_transfer_order,
    create_warehouse,
    get_inventory_balance,
    get_transfer_order_by_no,
    get_warehouse_by_code,
    list_inventory_balances,
    list_inventory_transactions,
    list_transfer_orders,
    list_warehouses,
    record_inventory_change,
)
from app.modules.store.models import Store
from tests.utils.utils import random_lower_string


def _make_store(db: Session) -> Store:
    store = Store(code=f"inv_{random_lower_string()[:8]}", name="库存测试门店")
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


def _make_warehouse(db: Session, store: Store, suffix: str = "") -> object:
    return create_warehouse(
        session=db,
        body=WarehouseCreate(
            store_id=store.id,
            code=f"WH{random_lower_string()[:6]}{suffix}",
            name="主仓库",
            warehouse_type="MAIN",
            is_active=True,
        ),
    )


# ---------------------------------------------------------------------------
# Warehouse
# ---------------------------------------------------------------------------


def test_create_warehouse(db: Session) -> None:
    store = _make_store(db)
    wh = _make_warehouse(db, store)
    assert wh.id is not None  # type: ignore[union-attr]
    assert wh.warehouse_type == "MAIN"  # type: ignore[union-attr]


def test_warehouse_code_unique_per_store(db: Session) -> None:
    store = _make_store(db)
    code = f"WH{random_lower_string()[:6]}"
    create_warehouse(
        session=db,
        body=WarehouseCreate(store_id=store.id, code=code, name="仓库1"),
    )
    found = get_warehouse_by_code(session=db, store_id=store.id, code=code)
    assert found is not None


def test_list_warehouses_by_store(db: Session) -> None:
    store = _make_store(db)
    _make_warehouse(db, store, "A")
    _make_warehouse(db, store, "B")
    whs = list_warehouses(session=db, store_id=store.id)
    assert len(whs) >= 2
    assert all(w.store_id == store.id for w in whs)


# ---------------------------------------------------------------------------
# Inventory changes & balance
# ---------------------------------------------------------------------------


def test_record_inventory_inbound(db: Session) -> None:
    import uuid

    store = _make_store(db)
    wh = _make_warehouse(db, store)
    sku_id = uuid.uuid4()

    tx = record_inventory_change(
        session=db,
        warehouse_id=wh.id,  # type: ignore[union-attr]
        sku_id=sku_id,
        transaction_type="IN",
        quantity=Decimal("100"),
        remark="首次入库",
    )
    assert tx.id is not None
    assert tx.transaction_type == "IN"
    assert tx.quantity == Decimal("100")
    assert tx.quantity_before == Decimal("0")
    assert tx.quantity_after == Decimal("100")

    # Balance updated
    balance = get_inventory_balance(session=db, warehouse_id=wh.id, sku_id=sku_id)  # type: ignore[union-attr]
    assert balance is not None
    assert balance.quantity == Decimal("100")


def test_record_inventory_outbound(db: Session) -> None:
    import uuid

    store = _make_store(db)
    wh = _make_warehouse(db, store)
    sku_id = uuid.uuid4()

    # First inbound
    record_inventory_change(
        session=db,
        warehouse_id=wh.id,  # type: ignore[union-attr]
        sku_id=sku_id,
        transaction_type="IN",
        quantity=Decimal("50"),
    )
    # Then outbound
    tx = record_inventory_change(
        session=db,
        warehouse_id=wh.id,  # type: ignore[union-attr]
        sku_id=sku_id,
        transaction_type="OUT",
        quantity=Decimal("-20"),
    )
    assert tx.quantity_before == Decimal("50")
    assert tx.quantity_after == Decimal("30")

    balance = get_inventory_balance(session=db, warehouse_id=wh.id, sku_id=sku_id)  # type: ignore[union-attr]
    assert balance is not None
    assert balance.quantity == Decimal("30")


def test_inventory_transaction_list(db: Session) -> None:
    import uuid

    store = _make_store(db)
    wh = _make_warehouse(db, store)
    sku_id = uuid.uuid4()

    record_inventory_change(
        session=db, warehouse_id=wh.id, sku_id=sku_id, transaction_type="IN", quantity=Decimal("10")  # type: ignore[union-attr]
    )
    record_inventory_change(
        session=db, warehouse_id=wh.id, sku_id=sku_id, transaction_type="IN", quantity=Decimal("5")  # type: ignore[union-attr]
    )

    txs = list_inventory_transactions(session=db, warehouse_id=wh.id)  # type: ignore[union-attr]
    assert len(txs) >= 2

    balances = list_inventory_balances(session=db, warehouse_id=wh.id)  # type: ignore[union-attr]
    assert len(balances) >= 1


# ---------------------------------------------------------------------------
# TransferOrder
# ---------------------------------------------------------------------------


def test_create_transfer_order(db: Session) -> None:
    store = _make_store(db)
    wh1 = _make_warehouse(db, store, "X")
    wh2 = _make_warehouse(db, store, "Y")
    transfer_no = f"TRF{random_lower_string()[:8]}"
    transfer = create_transfer_order(
        session=db,
        body=TransferOrderCreate(
            from_warehouse_id=wh1.id,  # type: ignore[union-attr]
            to_warehouse_id=wh2.id,  # type: ignore[union-attr]
            transfer_no=transfer_no,
            status="DRAFT",
        ),
    )
    assert transfer.id is not None
    assert transfer.status == "DRAFT"

    found = get_transfer_order_by_no(session=db, transfer_no=transfer_no)
    assert found is not None

    transfers = list_transfer_orders(session=db)
    assert len(transfers) >= 1


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------


def test_inventory_warehouse_api(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    store = _make_store(db)
    code = f"API_WH{random_lower_string()[:6]}"
    payload = {
        "store_id": str(store.id),
        "code": code,
        "name": "API仓库测试",
        "warehouse_type": "MAIN",
        "is_active": True,
    }
    resp = client.post(
        "/api/v1/inventory/warehouses",
        json=payload,
        headers=superuser_token_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "SUCCESS"
    assert data["data"]["code"] == code
    wh_id = data["data"]["id"]

    # List
    resp = client.get("/api/v1/inventory/warehouses", headers=superuser_token_headers)
    assert resp.status_code == 200

    # Update
    resp = client.patch(
        f"/api/v1/inventory/warehouses/{wh_id}",
        json={"name": "API仓库更新"},
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "API仓库更新"

    # List balances
    resp = client.get(
        f"/api/v1/inventory/warehouses/{wh_id}/balances",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200

    # List transactions
    resp = client.get(
        f"/api/v1/inventory/warehouses/{wh_id}/transactions",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200


def test_inventory_transfer_api(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    store = _make_store(db)
    wh1 = _make_warehouse(db, store, "P")
    wh2 = _make_warehouse(db, store, "Q")
    transfer_no = f"API_TRF{random_lower_string()[:6]}"

    resp = client.post(
        "/api/v1/inventory/transfers",
        json={
            "from_warehouse_id": str(wh1.id),  # type: ignore[union-attr]
            "to_warehouse_id": str(wh2.id),  # type: ignore[union-attr]
            "transfer_no": transfer_no,
            "status": "DRAFT",
        },
        headers=superuser_token_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "SUCCESS"
    assert data["data"]["transfer_no"] == transfer_no
    transfer_id = data["data"]["id"]

    # Confirm transfer
    resp = client.patch(
        f"/api/v1/inventory/transfers/{transfer_id}",
        json={"status": "CONFIRMED"},
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "CONFIRMED"
