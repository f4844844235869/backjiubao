import uuid

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import DataScopeDep, SessionDep, require_permissions
from app.core.response import ApiResponse, raise_api_error, success_response
from app.modules.pos.models import (
    OrderCreate,
    OrderItemCreate,
    OrderItemPublic,
    OrderPublic,
    OrderUpdate,
    PaymentCreate,
    PaymentPublic,
    ShiftHandoverCreate,
    ShiftHandoverPublic,
    ShiftHandoverUpdate,
)
from app.modules.pos.service import (
    create_order,
    create_order_item,
    create_payment,
    create_shift_handover,
    delete_order,
    delete_order_item,
    get_order_by_id,
    get_order_by_no,
    get_order_item_by_id,
    get_payment_by_id,
    get_shift_handover_by_id,
    list_order_items,
    list_orders,
    list_payments,
    list_shift_handovers,
    update_order,
    update_shift_handover,
)

router = APIRouter(prefix="/pos", tags=["POS"])


# ---------------------------------------------------------------------------
# Order Routes
# ---------------------------------------------------------------------------


@router.get(
    "/orders",
    summary="获取订单列表",
    dependencies=[Depends(require_permissions("pos.order.read"))],
    response_model=ApiResponse[list[OrderPublic]],
)
def read_orders(
    request: Request, session: SessionDep, scope: DataScopeDep
) -> ApiResponse[list[OrderPublic]]:
    store_id = scope.resolve_current_store_id(request=request)
    orders = list_orders(session=session, store_id=store_id)
    return success_response(
        request, data=[o.model_dump() for o in orders], message="获取订单列表成功"
    )


@router.post(
    "/orders",
    summary="创建订单",
    dependencies=[Depends(require_permissions("pos.order.create"))],
    response_model=ApiResponse[OrderPublic],
)
def create_order_route(
    request: Request, session: SessionDep, body: OrderCreate
) -> ApiResponse[OrderPublic]:
    existing = get_order_by_no(session=session, order_no=body.order_no)
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="ORDER_NO_EXISTS",
            message="订单编号已存在",
        )
    order = create_order(session=session, body=body)
    return success_response(
        request,
        data=order.model_dump(),
        message="创建订单成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/orders/{order_id}",
    summary="更新订单",
    dependencies=[Depends(require_permissions("pos.order.update"))],
    response_model=ApiResponse[OrderPublic],
)
def update_order_route(
    request: Request,
    session: SessionDep,
    order_id: uuid.UUID,
    body: OrderUpdate,
) -> ApiResponse[OrderPublic]:
    order = get_order_by_id(session=session, order_id=order_id)
    if not order:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ORDER_NOT_FOUND",
            message="订单不存在",
        )
    updated = update_order(
        session=session, order=order, data=body.model_dump(exclude_unset=True)
    )
    return success_response(request, data=updated.model_dump(), message="更新订单成功")


@router.delete(
    "/orders/{order_id}",
    summary="删除订单",
    dependencies=[Depends(require_permissions("pos.order.delete"))],
    response_model=ApiResponse[None],
)
def delete_order_route(
    request: Request, session: SessionDep, order_id: uuid.UUID
) -> ApiResponse[None]:
    order = get_order_by_id(session=session, order_id=order_id)
    if not order:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ORDER_NOT_FOUND",
            message="订单不存在",
        )
    delete_order(session=session, order=order)
    return success_response(request, data=None, message="删除订单成功")


# ---------------------------------------------------------------------------
# OrderItem Routes
# ---------------------------------------------------------------------------


@router.get(
    "/orders/{order_id}/items",
    summary="获取订单明细列表",
    dependencies=[Depends(require_permissions("pos.order.read"))],
    response_model=ApiResponse[list[OrderItemPublic]],
)
def read_order_items(
    request: Request, session: SessionDep, order_id: uuid.UUID
) -> ApiResponse[list[OrderItemPublic]]:
    items = list_order_items(session=session, order_id=order_id)
    return success_response(
        request, data=[i.model_dump() for i in items], message="获取订单明细成功"
    )


@router.post(
    "/orders/{order_id}/items",
    summary="新增订单明细",
    dependencies=[Depends(require_permissions("pos.order.create"))],
    response_model=ApiResponse[OrderItemPublic],
)
def create_order_item_route(
    request: Request,
    session: SessionDep,
    order_id: uuid.UUID,
    body: OrderItemCreate,
) -> ApiResponse[OrderItemPublic]:
    order = get_order_by_id(session=session, order_id=order_id)
    if not order:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ORDER_NOT_FOUND",
            message="订单不存在",
        )
    item = create_order_item(session=session, body=body)
    return success_response(
        request,
        data=item.model_dump(),
        message="新增订单明细成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.delete(
    "/orders/{order_id}/items/{item_id}",
    summary="删除订单明细",
    dependencies=[Depends(require_permissions("pos.order.delete"))],
    response_model=ApiResponse[None],
)
def delete_order_item_route(
    request: Request,
    session: SessionDep,
    order_id: uuid.UUID,
    item_id: uuid.UUID,
) -> ApiResponse[None]:
    item = get_order_item_by_id(session=session, item_id=item_id)
    if not item or item.order_id != order_id:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ORDER_ITEM_NOT_FOUND",
            message="订单明细不存在",
        )
    delete_order_item(session=session, item=item)
    return success_response(request, data=None, message="删除订单明细成功")


# ---------------------------------------------------------------------------
# Payment Routes
# ---------------------------------------------------------------------------


@router.get(
    "/orders/{order_id}/payments",
    summary="获取订单支付列表",
    dependencies=[Depends(require_permissions("pos.payment.read"))],
    response_model=ApiResponse[list[PaymentPublic]],
)
def read_payments(
    request: Request, session: SessionDep, order_id: uuid.UUID
) -> ApiResponse[list[PaymentPublic]]:
    payments = list_payments(session=session, order_id=order_id)
    return success_response(
        request, data=[p.model_dump() for p in payments], message="获取支付记录成功"
    )


@router.post(
    "/orders/{order_id}/payments",
    summary="创建支付记录",
    dependencies=[Depends(require_permissions("pos.payment.create"))],
    response_model=ApiResponse[PaymentPublic],
)
def create_payment_route(
    request: Request,
    session: SessionDep,
    order_id: uuid.UUID,
    body: PaymentCreate,
) -> ApiResponse[PaymentPublic]:
    order = get_order_by_id(session=session, order_id=order_id)
    if not order:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ORDER_NOT_FOUND",
            message="订单不存在",
        )
    payment = create_payment(session=session, body=body)
    return success_response(
        request,
        data=payment.model_dump(),
        message="创建支付记录成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.get(
    "/payments/{payment_id}",
    summary="获取支付详情",
    dependencies=[Depends(require_permissions("pos.payment.read"))],
    response_model=ApiResponse[PaymentPublic],
)
def read_payment(
    request: Request, session: SessionDep, payment_id: uuid.UUID
) -> ApiResponse[PaymentPublic]:
    payment = get_payment_by_id(session=session, payment_id=payment_id)
    if not payment:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PAYMENT_NOT_FOUND",
            message="支付记录不存在",
        )
    return success_response(request, data=payment.model_dump(), message="获取支付详情成功")


# ---------------------------------------------------------------------------
# ShiftHandover Routes
# ---------------------------------------------------------------------------


@router.get(
    "/shifts",
    summary="获取交接班列表",
    dependencies=[Depends(require_permissions("pos.shift.read"))],
    response_model=ApiResponse[list[ShiftHandoverPublic]],
)
def read_shifts(
    request: Request, session: SessionDep, scope: DataScopeDep
) -> ApiResponse[list[ShiftHandoverPublic]]:
    store_id = scope.resolve_current_store_id(request=request)
    shifts = list_shift_handovers(session=session, store_id=store_id)
    return success_response(
        request, data=[s.model_dump() for s in shifts], message="获取交接班列表成功"
    )


@router.post(
    "/shifts",
    summary="创建交接班",
    dependencies=[Depends(require_permissions("pos.shift.create"))],
    response_model=ApiResponse[ShiftHandoverPublic],
)
def create_shift_route(
    request: Request, session: SessionDep, body: ShiftHandoverCreate
) -> ApiResponse[ShiftHandoverPublic]:
    shift = create_shift_handover(session=session, body=body)
    return success_response(
        request,
        data=shift.model_dump(),
        message="创建交接班成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/shifts/{shift_id}",
    summary="更新交接班",
    dependencies=[Depends(require_permissions("pos.shift.update"))],
    response_model=ApiResponse[ShiftHandoverPublic],
)
def update_shift_route(
    request: Request,
    session: SessionDep,
    shift_id: uuid.UUID,
    body: ShiftHandoverUpdate,
) -> ApiResponse[ShiftHandoverPublic]:
    shift = get_shift_handover_by_id(session=session, shift_id=shift_id)
    if not shift:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="SHIFT_NOT_FOUND",
            message="交接班记录不存在",
        )
    updated = update_shift_handover(
        session=session, shift=shift, data=body.model_dump(exclude_unset=True)
    )
    return success_response(request, data=updated.model_dump(), message="更新交接班成功")
