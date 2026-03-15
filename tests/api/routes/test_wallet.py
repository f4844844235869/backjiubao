"""Tests for Member Wallet (会员钱包) module."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.modules.store.models import Store
from app.modules.wallet.service import (
    create_member,
    create_recharge_plan,
    get_gift_account,
    get_member_by_no,
    get_principal_account,
    list_wallet_transactions,
    recharge_member,
)
from tests.utils.utils import random_lower_string


def _make_store(db: Session) -> Store:
    store = Store(code=f"wlt_{random_lower_string()[:8]}", name="钱包测试门店")
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


# ---------------------------------------------------------------------------
# Member
# ---------------------------------------------------------------------------


def test_create_member_with_accounts(db: Session) -> None:
    store = _make_store(db)
    from app.modules.wallet.models import MemberCreate

    member = create_member(
        session=db,
        body=MemberCreate(
            store_id=store.id,
            member_no=f"M{random_lower_string()[:8]}",
            name="张三",
            mobile="13800138000",
            level="VIP",
        ),
    )
    assert member.id is not None
    assert member.level == "VIP"

    # Accounts should be auto-created
    principal = get_principal_account(session=db, member_id=member.id)
    assert principal is not None
    assert principal.balance == Decimal("0")

    gift = get_gift_account(session=db, member_id=member.id)
    assert gift is not None
    assert gift.balance == Decimal("0")


def test_member_no_unique(db: Session) -> None:
    store = _make_store(db)
    from app.modules.wallet.models import MemberCreate

    member_no = f"M{random_lower_string()[:8]}"
    create_member(
        session=db,
        body=MemberCreate(store_id=store.id, member_no=member_no, name="李四"),
    )
    found = get_member_by_no(session=db, member_no=member_no)
    assert found is not None
    assert found.name == "李四"


# ---------------------------------------------------------------------------
# Recharge
# ---------------------------------------------------------------------------


def test_recharge_member(db: Session) -> None:
    store = _make_store(db)
    from app.modules.wallet.models import MemberCreate, RechargePlanCreate

    member = create_member(
        session=db,
        body=MemberCreate(
            store_id=store.id,
            member_no=f"M{random_lower_string()[:8]}",
            name="充值测试会员",
        ),
    )
    plan = create_recharge_plan(
        session=db,
        body=RechargePlanCreate(
            store_id=store.id,
            name="100送20",
            recharge_amount=Decimal("100.00"),
            gift_amount=Decimal("20.00"),
            is_active=True,
        ),
    )

    principal_tx, gift_tx = recharge_member(session=db, member=member, plan=plan)

    # Check principal account balance updated
    principal = get_principal_account(session=db, member_id=member.id)
    assert principal is not None
    assert principal.balance == Decimal("100.00")
    assert principal.total_recharged == Decimal("100.00")

    # Check gift account balance updated
    gift = get_gift_account(session=db, member_id=member.id)
    assert gift is not None
    assert gift.balance == Decimal("20.00")
    assert gift.total_gifted == Decimal("20.00")

    # Transactions recorded
    assert principal_tx.transaction_type == "RECHARGE"
    assert principal_tx.amount == Decimal("100.00")
    assert gift_tx is not None
    assert gift_tx.transaction_type == "GIFT"
    assert gift_tx.amount == Decimal("20.00")


def test_recharge_without_gift(db: Session) -> None:
    store = _make_store(db)
    from app.modules.wallet.models import MemberCreate, RechargePlanCreate

    member = create_member(
        session=db,
        body=MemberCreate(
            store_id=store.id,
            member_no=f"M{random_lower_string()[:8]}",
            name="无赠金测试",
        ),
    )
    plan = create_recharge_plan(
        session=db,
        body=RechargePlanCreate(
            store_id=store.id,
            name="纯充值100",
            recharge_amount=Decimal("100.00"),
            gift_amount=Decimal("0"),
            is_active=True,
        ),
    )
    principal_tx, gift_tx = recharge_member(session=db, member=member, plan=plan)
    assert gift_tx is None
    principal = get_principal_account(session=db, member_id=member.id)
    assert principal is not None
    assert principal.balance == Decimal("100.00")


def test_wallet_transaction_history(db: Session) -> None:
    store = _make_store(db)
    from app.modules.wallet.models import MemberCreate, RechargePlanCreate

    member = create_member(
        session=db,
        body=MemberCreate(
            store_id=store.id,
            member_no=f"M{random_lower_string()[:8]}",
            name="流水测试",
        ),
    )
    plan = create_recharge_plan(
        session=db,
        body=RechargePlanCreate(
            store_id=store.id,
            name="50送10",
            recharge_amount=Decimal("50.00"),
            gift_amount=Decimal("10.00"),
        ),
    )
    recharge_member(session=db, member=member, plan=plan)
    recharge_member(session=db, member=member, plan=plan)

    txs = list_wallet_transactions(session=db, member_id=member.id)
    # 2 recharges * (1 principal + 1 gift) = 4 transactions
    assert len(txs) >= 4


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------


def test_wallet_member_api(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    store = _make_store(db)
    payload = {
        "store_id": str(store.id),
        "member_no": f"API_{random_lower_string()[:8]}",
        "name": "API会员",
        "level": "VIP",
    }
    resp = client.post(
        "/api/v1/wallet/members",
        json=payload,
        headers=superuser_token_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "SUCCESS"
    assert data["data"]["level"] == "VIP"
    member_id = data["data"]["id"]

    # Read principal account
    resp = client.get(
        f"/api/v1/wallet/members/{member_id}/principal-account",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["balance"] == "0.0"

    # Read gift account
    resp = client.get(
        f"/api/v1/wallet/members/{member_id}/gift-account",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200

    # List transactions (empty)
    resp = client.get(
        f"/api/v1/wallet/members/{member_id}/transactions",
        headers=superuser_token_headers,
    )
    assert resp.status_code == 200


def test_recharge_api(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    store = _make_store(db)
    from app.modules.wallet.models import MemberCreate, RechargePlanCreate

    member = create_member(
        session=db,
        body=MemberCreate(
            store_id=store.id,
            member_no=f"API_M{random_lower_string()[:8]}",
            name="API充值测试",
        ),
    )
    plan = create_recharge_plan(
        session=db,
        body=RechargePlanCreate(
            store_id=store.id,
            name="API充值方案",
            recharge_amount=Decimal("200.00"),
            gift_amount=Decimal("30.00"),
            is_active=True,
        ),
    )

    resp = client.post(
        "/api/v1/wallet/recharge",
        json={"member_id": str(member.id), "recharge_plan_id": str(plan.id)},
        headers=superuser_token_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "SUCCESS"
    assert data["data"]["transaction_type"] == "RECHARGE"
