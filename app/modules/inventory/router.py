import uuid

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import DataScopeDep, SessionDep, require_permissions
from app.core.response import ApiResponse, raise_api_error, success_response
from app.modules.inventory.models import (
    InventoryBalancePublic,
    InventoryTransactionCreate,
    InventoryTransactionPublic,
    TransferOrderCreate,
    TransferOrderPublic,
    TransferOrderUpdate,
    WarehouseCreate,
    WarehousePublic,
    WarehouseUpdate,
)
from app.modules.inventory.service import (
    create_transfer_order,
    create_warehouse,
    delete_warehouse,
    get_transfer_order_by_id,
    get_transfer_order_by_no,
    get_warehouse_by_code,
    get_warehouse_by_id,
    list_inventory_balances,
    list_inventory_transactions,
    list_transfer_orders,
    list_warehouses,
    record_inventory_change,
    update_transfer_order,
    update_warehouse,
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ---------------------------------------------------------------------------
# Warehouse Routes
# ---------------------------------------------------------------------------


@router.get(
    "/warehouses",
    summary="获取仓库列表",
    dependencies=[Depends(require_permissions("inventory.warehouse.read"))],
    response_model=ApiResponse[list[WarehousePublic]],
)
def read_warehouses(
    request: Request, session: SessionDep, scope: DataScopeDep
) -> ApiResponse[list[WarehousePublic]]:
    store_id = scope.resolve_current_store_id(request=request)
    warehouses = list_warehouses(session=session, store_id=store_id)
    return success_response(
        request, data=[w.model_dump() for w in warehouses], message="获取仓库列表成功"
    )


@router.post(
    "/warehouses",
    summary="创建仓库",
    dependencies=[Depends(require_permissions("inventory.warehouse.create"))],
    response_model=ApiResponse[WarehousePublic],
)
def create_warehouse_route(
    request: Request, session: SessionDep, body: WarehouseCreate
) -> ApiResponse[WarehousePublic]:
    existing = get_warehouse_by_code(
        session=session, store_id=body.store_id, code=body.code
    )
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="WAREHOUSE_CODE_EXISTS",
            message="仓库编码在该门店中已存在",
        )
    warehouse = create_warehouse(session=session, body=body)
    return success_response(
        request,
        data=warehouse.model_dump(),
        message="创建仓库成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/warehouses/{warehouse_id}",
    summary="更新仓库",
    dependencies=[Depends(require_permissions("inventory.warehouse.update"))],
    response_model=ApiResponse[WarehousePublic],
)
def update_warehouse_route(
    request: Request,
    session: SessionDep,
    warehouse_id: uuid.UUID,
    body: WarehouseUpdate,
) -> ApiResponse[WarehousePublic]:
    warehouse = get_warehouse_by_id(session=session, warehouse_id=warehouse_id)
    if not warehouse:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="WAREHOUSE_NOT_FOUND",
            message="仓库不存在",
        )
    updated = update_warehouse(
        session=session, warehouse=warehouse, data=body.model_dump(exclude_unset=True)
    )
    return success_response(request, data=updated.model_dump(), message="更新仓库成功")


@router.delete(
    "/warehouses/{warehouse_id}",
    summary="删除仓库",
    dependencies=[Depends(require_permissions("inventory.warehouse.delete"))],
    response_model=ApiResponse[None],
)
def delete_warehouse_route(
    request: Request, session: SessionDep, warehouse_id: uuid.UUID
) -> ApiResponse[None]:
    warehouse = get_warehouse_by_id(session=session, warehouse_id=warehouse_id)
    if not warehouse:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="WAREHOUSE_NOT_FOUND",
            message="仓库不存在",
        )
    delete_warehouse(session=session, warehouse=warehouse)
    return success_response(request, data=None, message="删除仓库成功")


# ---------------------------------------------------------------------------
# InventoryBalance Routes
# ---------------------------------------------------------------------------


@router.get(
    "/warehouses/{warehouse_id}/balances",
    summary="获取库存余额列表",
    dependencies=[Depends(require_permissions("inventory.balance.read"))],
    response_model=ApiResponse[list[InventoryBalancePublic]],
)
def read_inventory_balances(
    request: Request, session: SessionDep, warehouse_id: uuid.UUID
) -> ApiResponse[list[InventoryBalancePublic]]:
    balances = list_inventory_balances(session=session, warehouse_id=warehouse_id)
    return success_response(
        request,
        data=[b.model_dump() for b in balances],
        message="获取库存余额列表成功",
    )


# ---------------------------------------------------------------------------
# InventoryTransaction Routes
# ---------------------------------------------------------------------------


@router.get(
    "/warehouses/{warehouse_id}/transactions",
    summary="获取库存流水列表",
    dependencies=[Depends(require_permissions("inventory.transaction.read"))],
    response_model=ApiResponse[list[InventoryTransactionPublic]],
)
def read_inventory_transactions(
    request: Request, session: SessionDep, warehouse_id: uuid.UUID
) -> ApiResponse[list[InventoryTransactionPublic]]:
    txs = list_inventory_transactions(session=session, warehouse_id=warehouse_id)
    return success_response(
        request, data=[tx.model_dump() for tx in txs], message="获取库存流水列表成功"
    )


@router.post(
    "/transactions",
    summary="记录库存变动",
    dependencies=[Depends(require_permissions("inventory.transaction.create"))],
    response_model=ApiResponse[InventoryTransactionPublic],
)
def create_inventory_transaction_route(
    request: Request, session: SessionDep, body: InventoryTransactionCreate
) -> ApiResponse[InventoryTransactionPublic]:
    tx = record_inventory_change(
        session=session,
        warehouse_id=body.warehouse_id,
        sku_id=body.sku_id,
        transaction_type=body.transaction_type,
        quantity=body.quantity,
        ref_order_id=body.ref_order_id,
        operator_id=body.operator_id,
        remark=body.remark,
    )
    return success_response(
        request,
        data=tx.model_dump(),
        message="记录库存变动成功",
        status_code=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# TransferOrder Routes
# ---------------------------------------------------------------------------


@router.get(
    "/transfers",
    summary="获取调拨单列表",
    dependencies=[Depends(require_permissions("inventory.transfer.read"))],
    response_model=ApiResponse[list[TransferOrderPublic]],
)
def read_transfer_orders(
    request: Request, session: SessionDep
) -> ApiResponse[list[TransferOrderPublic]]:
    transfers = list_transfer_orders(session=session)
    return success_response(
        request,
        data=[t.model_dump() for t in transfers],
        message="获取调拨单列表成功",
    )


@router.post(
    "/transfers",
    summary="创建调拨单",
    dependencies=[Depends(require_permissions("inventory.transfer.create"))],
    response_model=ApiResponse[TransferOrderPublic],
)
def create_transfer_order_route(
    request: Request, session: SessionDep, body: TransferOrderCreate
) -> ApiResponse[TransferOrderPublic]:
    existing = get_transfer_order_by_no(session=session, transfer_no=body.transfer_no)
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="TRANSFER_NO_EXISTS",
            message="调拨单编号已存在",
        )
    transfer = create_transfer_order(session=session, body=body)
    return success_response(
        request,
        data=transfer.model_dump(),
        message="创建调拨单成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/transfers/{transfer_id}",
    summary="更新调拨单",
    dependencies=[Depends(require_permissions("inventory.transfer.update"))],
    response_model=ApiResponse[TransferOrderPublic],
)
def update_transfer_order_route(
    request: Request,
    session: SessionDep,
    transfer_id: uuid.UUID,
    body: TransferOrderUpdate,
) -> ApiResponse[TransferOrderPublic]:
    transfer = get_transfer_order_by_id(session=session, transfer_id=transfer_id)
    if not transfer:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="TRANSFER_NOT_FOUND",
            message="调拨单不存在",
        )
    updated = update_transfer_order(
        session=session, transfer=transfer, data=body.model_dump(exclude_unset=True)
    )
    return success_response(request, data=updated.model_dump(), message="更新调拨单成功")
