import uuid
from decimal import Decimal

from sqlmodel import Session, select

from app.modules.wallet.models import (
    GiftAccount,
    Member,
    MemberCreate,
    PrincipalAccount,
    RechargePlan,
    RechargePlanCreate,
    WalletTransaction,
    WalletTransactionCreate,
)

# ---------------------------------------------------------------------------
# Member
# ---------------------------------------------------------------------------


def list_members(
    *, session: Session, store_id: uuid.UUID | None = None
) -> list[Member]:
    statement = select(Member).order_by(Member.created_at)
    if store_id:
        statement = statement.where(Member.store_id == store_id)
    return list(session.exec(statement).all())


def get_member_by_id(*, session: Session, member_id: uuid.UUID) -> Member | None:
    return session.get(Member, member_id)


def get_member_by_no(*, session: Session, member_no: str) -> Member | None:
    return session.exec(select(Member).where(Member.member_no == member_no)).first()


def create_member(*, session: Session, body: MemberCreate) -> Member:
    member = Member.model_validate(body)
    session.add(member)
    session.flush()  # Get member ID before creating accounts
    # Auto-create principal and gift accounts
    principal = PrincipalAccount(member_id=member.id)
    gift = GiftAccount(member_id=member.id)
    session.add(principal)
    session.add(gift)
    session.commit()
    session.refresh(member)
    return member


def update_member(*, session: Session, member: Member, data: dict) -> Member:
    from app.models.base import get_datetime_utc

    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(member, key, value)
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


def delete_member(*, session: Session, member: Member) -> None:
    session.delete(member)
    session.commit()


# ---------------------------------------------------------------------------
# Account helpers
# ---------------------------------------------------------------------------


def get_principal_account(
    *, session: Session, member_id: uuid.UUID
) -> PrincipalAccount | None:
    return session.exec(
        select(PrincipalAccount).where(PrincipalAccount.member_id == member_id)
    ).first()


def get_gift_account(
    *, session: Session, member_id: uuid.UUID
) -> GiftAccount | None:
    return session.exec(
        select(GiftAccount).where(GiftAccount.member_id == member_id)
    ).first()


# ---------------------------------------------------------------------------
# RechargePlan
# ---------------------------------------------------------------------------


def list_recharge_plans(
    *, session: Session, store_id: uuid.UUID | None = None
) -> list[RechargePlan]:
    statement = select(RechargePlan).order_by(RechargePlan.created_at)
    if store_id:
        statement = statement.where(RechargePlan.store_id == store_id)
    return list(session.exec(statement).all())


def get_recharge_plan_by_id(
    *, session: Session, plan_id: uuid.UUID
) -> RechargePlan | None:
    return session.get(RechargePlan, plan_id)


def create_recharge_plan(*, session: Session, body: RechargePlanCreate) -> RechargePlan:
    plan = RechargePlan.model_validate(body)
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


def update_recharge_plan(
    *, session: Session, plan: RechargePlan, data: dict
) -> RechargePlan:
    from app.models.base import get_datetime_utc

    data["updated_at"] = get_datetime_utc()
    for key, value in data.items():
        setattr(plan, key, value)
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


def delete_recharge_plan(*, session: Session, plan: RechargePlan) -> None:
    session.delete(plan)
    session.commit()


# ---------------------------------------------------------------------------
# Recharge (top-up operation)
# ---------------------------------------------------------------------------


def recharge_member(
    *,
    session: Session,
    member: Member,
    plan: RechargePlan,
    operator_id: uuid.UUID | None = None,
    remark: str | None = None,
) -> tuple[WalletTransaction, WalletTransaction | None]:
    """Recharge member principal account and optionally add gift amount."""
    principal = get_principal_account(session=session, member_id=member.id)
    if not principal:
        raise ValueError("PRINCIPAL_ACCOUNT_NOT_FOUND")

    balance_before = principal.balance
    principal.balance += plan.recharge_amount
    principal.total_recharged += plan.recharge_amount
    session.add(principal)

    # Record principal transaction
    principal_tx = WalletTransaction(
        member_id=member.id,
        account_type="PRINCIPAL",
        transaction_type="RECHARGE",
        amount=plan.recharge_amount,
        balance_before=balance_before,
        balance_after=principal.balance,
        remark=remark,
        operator_id=operator_id,
    )
    session.add(principal_tx)

    gift_tx: WalletTransaction | None = None
    if plan.gift_amount and plan.gift_amount > Decimal("0"):
        gift = get_gift_account(session=session, member_id=member.id)
        if gift:
            gift_balance_before = gift.balance
            gift.balance += plan.gift_amount
            gift.total_gifted += plan.gift_amount
            session.add(gift)

            gift_tx = WalletTransaction(
                member_id=member.id,
                account_type="GIFT",
                transaction_type="GIFT",
                amount=plan.gift_amount,
                balance_before=gift_balance_before,
                balance_after=gift.balance,
                remark=remark,
                operator_id=operator_id,
            )
            session.add(gift_tx)

    session.commit()
    session.refresh(principal_tx)
    return principal_tx, gift_tx


# ---------------------------------------------------------------------------
# WalletTransaction
# ---------------------------------------------------------------------------


def list_wallet_transactions(
    *, session: Session, member_id: uuid.UUID | None = None
) -> list[WalletTransaction]:
    statement = select(WalletTransaction).order_by(WalletTransaction.created_at.desc())
    if member_id:
        statement = statement.where(WalletTransaction.member_id == member_id)
    return list(session.exec(statement).all())


def create_wallet_transaction(
    *, session: Session, body: WalletTransactionCreate
) -> WalletTransaction:
    tx = WalletTransaction.model_validate(body)
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx
