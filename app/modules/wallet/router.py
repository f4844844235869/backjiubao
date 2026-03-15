import uuid

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import DataScopeDep, SessionDep, require_permissions
from app.core.response import ApiResponse, raise_api_error, success_response
from app.modules.wallet.models import (
    GiftAccountPublic,
    MemberCreate,
    MemberPublic,
    MemberUpdate,
    PrincipalAccountPublic,
    RechargePlanCreate,
    RechargePlanPublic,
    RechargePlanUpdate,
    RechargeRequest,
    WalletTransactionPublic,
)
from app.modules.wallet.service import (
    create_member,
    create_recharge_plan,
    delete_member,
    delete_recharge_plan,
    get_gift_account,
    get_member_by_id,
    get_member_by_no,
    get_principal_account,
    get_recharge_plan_by_id,
    list_members,
    list_recharge_plans,
    list_wallet_transactions,
    recharge_member,
    update_member,
    update_recharge_plan,
)

router = APIRouter(prefix="/wallet", tags=["Member Wallet"])


# ---------------------------------------------------------------------------
# Member Routes
# ---------------------------------------------------------------------------


@router.get(
    "/members",
    summary="获取会员列表",
    dependencies=[Depends(require_permissions("wallet.member.read"))],
    response_model=ApiResponse[list[MemberPublic]],
)
def read_members(
    request: Request, session: SessionDep, scope: DataScopeDep
) -> ApiResponse[list[MemberPublic]]:
    store_id = scope.resolve_current_store_id(request=request)
    members = list_members(session=session, store_id=store_id)
    return success_response(
        request, data=[m.model_dump() for m in members], message="获取会员列表成功"
    )


@router.post(
    "/members",
    summary="创建会员",
    dependencies=[Depends(require_permissions("wallet.member.create"))],
    response_model=ApiResponse[MemberPublic],
)
def create_member_route(
    request: Request, session: SessionDep, body: MemberCreate
) -> ApiResponse[MemberPublic]:
    existing = get_member_by_no(session=session, member_no=body.member_no)
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="MEMBER_NO_EXISTS",
            message="会员编号已存在",
        )
    member = create_member(session=session, body=body)
    return success_response(
        request,
        data=member.model_dump(),
        message="创建会员成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/members/{member_id}",
    summary="更新会员",
    dependencies=[Depends(require_permissions("wallet.member.update"))],
    response_model=ApiResponse[MemberPublic],
)
def update_member_route(
    request: Request,
    session: SessionDep,
    member_id: uuid.UUID,
    body: MemberUpdate,
) -> ApiResponse[MemberPublic]:
    member = get_member_by_id(session=session, member_id=member_id)
    if not member:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="MEMBER_NOT_FOUND",
            message="会员不存在",
        )
    updated = update_member(
        session=session, member=member, data=body.model_dump(exclude_unset=True)
    )
    return success_response(request, data=updated.model_dump(), message="更新会员成功")


@router.delete(
    "/members/{member_id}",
    summary="删除会员",
    dependencies=[Depends(require_permissions("wallet.member.delete"))],
    response_model=ApiResponse[None],
)
def delete_member_route(
    request: Request, session: SessionDep, member_id: uuid.UUID
) -> ApiResponse[None]:
    member = get_member_by_id(session=session, member_id=member_id)
    if not member:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="MEMBER_NOT_FOUND",
            message="会员不存在",
        )
    delete_member(session=session, member=member)
    return success_response(request, data=None, message="删除会员成功")


# ---------------------------------------------------------------------------
# Account Routes
# ---------------------------------------------------------------------------


@router.get(
    "/members/{member_id}/principal-account",
    summary="获取本金账户",
    dependencies=[Depends(require_permissions("wallet.account.read"))],
    response_model=ApiResponse[PrincipalAccountPublic],
)
def read_principal_account(
    request: Request, session: SessionDep, member_id: uuid.UUID
) -> ApiResponse[PrincipalAccountPublic]:
    account = get_principal_account(session=session, member_id=member_id)
    if not account:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ACCOUNT_NOT_FOUND",
            message="本金账户不存在",
        )
    return success_response(request, data=account.model_dump(), message="获取本金账户成功")


@router.get(
    "/members/{member_id}/gift-account",
    summary="获取赠金账户",
    dependencies=[Depends(require_permissions("wallet.account.read"))],
    response_model=ApiResponse[GiftAccountPublic],
)
def read_gift_account(
    request: Request, session: SessionDep, member_id: uuid.UUID
) -> ApiResponse[GiftAccountPublic]:
    account = get_gift_account(session=session, member_id=member_id)
    if not account:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ACCOUNT_NOT_FOUND",
            message="赠金账户不存在",
        )
    return success_response(request, data=account.model_dump(), message="获取赠金账户成功")


# ---------------------------------------------------------------------------
# RechargePlan Routes
# ---------------------------------------------------------------------------


@router.get(
    "/recharge-plans",
    summary="获取充值方案列表",
    dependencies=[Depends(require_permissions("wallet.recharge_plan.read"))],
    response_model=ApiResponse[list[RechargePlanPublic]],
)
def read_recharge_plans(
    request: Request, session: SessionDep, scope: DataScopeDep
) -> ApiResponse[list[RechargePlanPublic]]:
    store_id = scope.resolve_current_store_id(request=request)
    plans = list_recharge_plans(session=session, store_id=store_id)
    return success_response(
        request, data=[p.model_dump() for p in plans], message="获取充值方案列表成功"
    )


@router.post(
    "/recharge-plans",
    summary="创建充值方案",
    dependencies=[Depends(require_permissions("wallet.recharge_plan.create"))],
    response_model=ApiResponse[RechargePlanPublic],
)
def create_recharge_plan_route(
    request: Request, session: SessionDep, body: RechargePlanCreate
) -> ApiResponse[RechargePlanPublic]:
    plan = create_recharge_plan(session=session, body=body)
    return success_response(
        request,
        data=plan.model_dump(),
        message="创建充值方案成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/recharge-plans/{plan_id}",
    summary="更新充值方案",
    dependencies=[Depends(require_permissions("wallet.recharge_plan.update"))],
    response_model=ApiResponse[RechargePlanPublic],
)
def update_recharge_plan_route(
    request: Request,
    session: SessionDep,
    plan_id: uuid.UUID,
    body: RechargePlanUpdate,
) -> ApiResponse[RechargePlanPublic]:
    plan = get_recharge_plan_by_id(session=session, plan_id=plan_id)
    if not plan:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RECHARGE_PLAN_NOT_FOUND",
            message="充值方案不存在",
        )
    updated = update_recharge_plan(
        session=session, plan=plan, data=body.model_dump(exclude_unset=True)
    )
    return success_response(request, data=updated.model_dump(), message="更新充值方案成功")


@router.delete(
    "/recharge-plans/{plan_id}",
    summary="删除充值方案",
    dependencies=[Depends(require_permissions("wallet.recharge_plan.delete"))],
    response_model=ApiResponse[None],
)
def delete_recharge_plan_route(
    request: Request, session: SessionDep, plan_id: uuid.UUID
) -> ApiResponse[None]:
    plan = get_recharge_plan_by_id(session=session, plan_id=plan_id)
    if not plan:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RECHARGE_PLAN_NOT_FOUND",
            message="充值方案不存在",
        )
    delete_recharge_plan(session=session, plan=plan)
    return success_response(request, data=None, message="删除充值方案成功")


# ---------------------------------------------------------------------------
# Recharge Route
# ---------------------------------------------------------------------------


@router.post(
    "/recharge",
    summary="会员充值",
    dependencies=[Depends(require_permissions("wallet.recharge.create"))],
    response_model=ApiResponse[WalletTransactionPublic],
)
def recharge_route(
    request: Request, session: SessionDep, body: RechargeRequest
) -> ApiResponse[WalletTransactionPublic]:
    member = get_member_by_id(session=session, member_id=body.member_id)
    if not member:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="MEMBER_NOT_FOUND",
            message="会员不存在",
        )
    plan = get_recharge_plan_by_id(session=session, plan_id=body.recharge_plan_id)
    if not plan:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RECHARGE_PLAN_NOT_FOUND",
            message="充值方案不存在",
        )
    if not plan.is_active:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="RECHARGE_PLAN_INACTIVE",
            message="充值方案已停用",
        )
    principal_tx, _ = recharge_member(
        session=session,
        member=member,
        plan=plan,
        operator_id=body.operator_id,
        remark=body.remark,
    )
    return success_response(
        request,
        data=principal_tx.model_dump(),
        message="充值成功",
        status_code=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# WalletTransaction Routes
# ---------------------------------------------------------------------------


@router.get(
    "/members/{member_id}/transactions",
    summary="获取会员钱包流水",
    dependencies=[Depends(require_permissions("wallet.transaction.read"))],
    response_model=ApiResponse[list[WalletTransactionPublic]],
)
def read_wallet_transactions(
    request: Request, session: SessionDep, member_id: uuid.UUID
) -> ApiResponse[list[WalletTransactionPublic]]:
    txs = list_wallet_transactions(session=session, member_id=member_id)
    return success_response(
        request, data=[tx.model_dump() for tx in txs], message="获取钱包流水成功"
    )
