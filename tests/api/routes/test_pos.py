"""Tests for POS module."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.modules.pos.models import (
    OrderCreate,
    OrderItemCreate,
    PaymentCreate,
    ShiftHandoverCreate,
)
from app.modules.pos.service import (
    create_order,
    create_order_item,
    create_payment,
    create_shift_handover,
    get_order_by_no,
    list_order_items,
    list_payments,
    list_shift_handovers,
    update_order,
)
from app.modules.store.models import Store
from tests.utils.utils import random_lower_string


def _make_store(db: Session) -> Store:
    store = Store(code=f"pos_{random_lower_string()[:8]}", name="POS测试门店")
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


def _make_order(db: Session, store: Store, suffix: str = "") -> object:
    return create_order(
        session=db,
        body=OrderCreate(
            store_id=store.id,
            order_no=f"ORD{random_lower_string()[:8]}{suffix}",
            total_amount=Decimal("100.00"),
            payable_amount=Decimal("100.00"),
            status="PENDING",
        ),
    )


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------


def test_create_order(db: Session) -> None:
    store = _make_store(db)
    order = _make_order(db, store)
    assert order.id is not None  # type: ignore[union-attr]
    assert order.status == "PENDING"  # type: ignore[union-attr]


def test_get_order_by_no(db: Session) -> None:
    store = _make_store(db)
    order_no = f"ORD{random_lower_string()[:8]}"
    create_order(
        session=db,
        body=OrderCreate(
            store_id=store.id,
            order_no=order_no,
            total_amount=Decimal("50.00"),
            payable_amount=Decimal("50.00"),
        ),
    )
    found = get_order_by_no(session=db, order_no=order_no)
    assert found is not None
    assert found.order_no == order_no


def test_update_order_status(db: Session) -> None:
    store = _make_store(db)
    order = _make_order(db, store)
    updated = update_order(
        session=db, order=order, data={"status": "PAID", "paid_amount": Decimal("100.00")}  # type: ignore[arg-type]
    )
    assert updated.status == "PAID"
    assert updated.paid_amount == Decimal("100.00")


# ---------------------------------------------------------------------------
# OrderItem
# ---------------------------------------------------------------------------


def test_create_order_item(db: Session) -> None:
    store = _make_store(db)
    order = _make_order(db, store)
    item = create_order_item(
        session=db,
        body=OrderItemCreate(
            order_id=order.id,  # type: ignore[union-attr]
            product_name="茅台",
            unit_price=Decimal("1899.00"),
            quantity=Decimal("2"),
            subtotal=Decimal("3798.00"),
        ),
    )
    assert item.id is not None
    assert item.product_name == "茅台"
    assert item.subtotal == Decimal("3798.00")

    items = list_order_items(session=db, order_id=order.id)  # type: ignore[union-attr]
    assert len(items) >= 1


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------


def test_create_payment(db: Session) -> None:
    store = _make_store(db)
    order = _make_order(db, store)
    payment = create_payment(
        session=db,
        body=PaymentCreate(
            order_id=order.id,  # type: ignore[union-attr]
            payment_method="CASH",
            amount=Decimal("100.00"),
            status="SUCCESS",
        ),
    )
    assert payment.id is not None
    assert payment.payment_method == "CASH"
    assert payment.amount == Decimal("100.00")

    payments = list_payments(session=db, order_id=order.id)  # type: ignore[union-attr]
    assert len(payments) >= 1


# ---------------------------------------------------------------------------
# ShiftHandover
# ---------------------------------------------------------------------------


def test_create_shift_handover(db: Session) -> None:
    from datetime import datetime, timezone

    store = _make_store(db)
    from app import crud
    from app.models import UserCreate
    from tests.utils.utils import random_email

    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            username=random_lower_string(),
            email=random_email(),
            password="password1234",
        ),
    )
    shift = create_shift_handover(
        session=db,
        body=ShiftHandoverCreate(
            store_id=store.id,
            shift_date=datetime.now(timezone.utc),
            shift_type="MORNING",
            operator_id=user.id,
            cash_amount=Decimal("500.00"),
            total_sales=Decimal("2300.00"),
            order_count=15,
            status="OPEN",
        ),
    )
    assert shift.id is not None
    assert shift.status == "OPEN"
    assert shift.order_count == 15

    shifts = list_shift_handovers(session=db, store_id=store.id)
    assert len(shifts) >= 1


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------


def test_pos_order_api(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    store = _make_store(db)
    order_no = f"API_ORD{random_lower_string()[:6]}"
    payload = {
        "store_id": str(store.id),
        "order_no": order_no,
        "total_amount": "150.00",
        "payable_amount": "150.00",
        "status": "PENDING",
    }
    resp = client.post(
        "/api/v1/pos/orders",
        json=payload,
        headers=superuser_token_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "SUCCESS"
    assert data["data"]["order_no"] == order_no
    order_id = data["data"]["id"]

    # Update order
    resp = client.patch(
        f"/api/v1/pos/orders/{order_id}",
        json={"status": "PAID", "paid_amount": "150.00"},
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "PAID"

    # List orders
    resp = client.get("/api/v1/pos/orders", headers=superuser_token_headers)
    assert resp.status_code == 200

    # Add order item
    resp = client.post(
        f"/api/v1/pos/orders/{order_id}/items",
        json={
            "order_id": order_id,
            "product_name": "测试商品",
            "unit_price": "75.00",
            "quantity": "2",
            "subtotal": "150.00",
        },
        headers=superuser_token_headers,
    )
    assert resp.status_code == 201

    # List items
    resp = client.get(
        f"/api/v1/pos/orders/{order_id}/items",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200

    # Create payment
    resp = client.post(
        f"/api/v1/pos/orders/{order_id}/payments",
        json={
            "order_id": order_id,
            "payment_method": "CASH",
            "amount": "150.00",
            "status": "SUCCESS",
        },
        headers=superuser_token_headers,
    )
    assert resp.status_code == 201
