import uuid

from sqlmodel import Session, select

from app.modules.pos.models import (
    Order,
    OrderCreate,
    OrderItem,
    OrderItemCreate,
    Payment,
    PaymentCreate,
    ShiftHandover,
    ShiftHandoverCreate,
)

# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------


def list_orders(
    *, session: Session, store_id: uuid.UUID | None = None
) -> list[Order]:
    statement = select(Order).order_by(Order.created_at.desc())
    if store_id:
        statement = statement.where(Order.store_id == store_id)
    return list(session.exec(statement).all())


def get_order_by_id(*, session: Session, order_id: uuid.UUID) -> Order | None:
    return session.get(Order, order_id)


def get_order_by_no(*, session: Session, order_no: str) -> Order | None:
    return session.exec(select(Order).where(Order.order_no == order_no)).first()


def create_order(*, session: Session, body: OrderCreate) -> Order:
    order = Order.model_validate(body)
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def update_order(*, session: Session, order: Order, data: dict) -> Order:
    from app.models.base import get_datetime_utc

    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(order, key, value)
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def delete_order(*, session: Session, order: Order) -> None:
    session.delete(order)
    session.commit()


# ---------------------------------------------------------------------------
# OrderItem
# ---------------------------------------------------------------------------


def list_order_items(
    *, session: Session, order_id: uuid.UUID
) -> list[OrderItem]:
    return list(
        session.exec(
            select(OrderItem).where(OrderItem.order_id == order_id)
        ).all()
    )


def get_order_item_by_id(
    *, session: Session, item_id: uuid.UUID
) -> OrderItem | None:
    return session.get(OrderItem, item_id)


def create_order_item(*, session: Session, body: OrderItemCreate) -> OrderItem:
    item = OrderItem.model_validate(body)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def delete_order_item(*, session: Session, item: OrderItem) -> None:
    session.delete(item)
    session.commit()


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------


def list_payments(
    *, session: Session, order_id: uuid.UUID
) -> list[Payment]:
    return list(
        session.exec(
            select(Payment).where(Payment.order_id == order_id)
        ).all()
    )


def get_payment_by_id(
    *, session: Session, payment_id: uuid.UUID
) -> Payment | None:
    return session.get(Payment, payment_id)


def create_payment(*, session: Session, body: PaymentCreate) -> Payment:
    payment = Payment.model_validate(body)
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment


# ---------------------------------------------------------------------------
# ShiftHandover
# ---------------------------------------------------------------------------


def list_shift_handovers(
    *, session: Session, store_id: uuid.UUID | None = None
) -> list[ShiftHandover]:
    statement = select(ShiftHandover).order_by(ShiftHandover.shift_date.desc())
    if store_id:
        statement = statement.where(ShiftHandover.store_id == store_id)
    return list(session.exec(statement).all())


def get_shift_handover_by_id(
    *, session: Session, shift_id: uuid.UUID
) -> ShiftHandover | None:
    return session.get(ShiftHandover, shift_id)


def create_shift_handover(*, session: Session, body: ShiftHandoverCreate) -> ShiftHandover:
    shift = ShiftHandover.model_validate(body)
    session.add(shift)
    session.commit()
    session.refresh(shift)
    return shift


def update_shift_handover(
    *, session: Session, shift: ShiftHandover, data: dict
) -> ShiftHandover:
    from app.models.base import get_datetime_utc

    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(shift, key, value)
    session.add(shift)
    session.commit()
    session.refresh(shift)
    return shift
