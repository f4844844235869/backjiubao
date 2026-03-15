import uuid

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import DataScopeDep, SessionDep, require_permissions
from app.core.response import ApiResponse, raise_api_error, success_response
from app.modules.store.models import StoreCreate, StorePublic, StoreUpdate
from app.modules.store.service import (
    check_store_deletion_references,
    create_store,
    delete_store,
    get_store_by_code,
    get_store_by_id,
    list_stores,
    update_store,
)

router = APIRouter(prefix="/stores", tags=["Stores"])


@router.get(
    "/",
    summary="获取门店列表",
    dependencies=[Depends(require_permissions("org.store.read"))],
    response_model=ApiResponse[list[StorePublic]],
)
def read_stores(request: Request, session: SessionDep, scope: DataScopeDep):
    stores = list_stores(session=session)
    current_store_id = scope.resolve_current_store_id(request=request)
    if not scope.current_user.is_superuser:
        allowed_store_ids = scope.allowed_store_ids()
        stores = [store for store in stores if store.id in allowed_store_ids]
    if current_store_id:
        stores = [store for store in stores if store.id == current_store_id]
    return success_response(
        request,
        data=[store.model_dump() for store in stores],
        message="获取门店列表成功",
    )


@router.post(
    "/",
    summary="创建门店",
    dependencies=[Depends(require_permissions("org.store.create"))],
    response_model=ApiResponse[StorePublic],
)
def create_store_route(request: Request, session: SessionDep, body: StoreCreate):
    existing = get_store_by_code(session=session, code=body.code)
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="STORE_CODE_EXISTS",
            message="门店编码已存在",
        )
    store = create_store(session=session, body=body)
    return success_response(
        request,
        data=store.model_dump(),
        message="创建门店成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/{store_id}",
    summary="更新门店",
    dependencies=[Depends(require_permissions("org.store.update"))],
    response_model=ApiResponse[StorePublic],
)
def update_store_route(
    request: Request,
    session: SessionDep,
    store_id: uuid.UUID,
    body: StoreUpdate,
    scope: DataScopeDep,
):
    store = get_store_by_id(session=session, store_id=store_id)
    if not store:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="STORE_NOT_FOUND",
            message="门店不存在",
        )
    current_store_id = scope.resolve_current_store_id(request=request)
    if current_store_id and store.id != current_store_id:
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前门店上下文不允许修改其他门店",
        )
    if not scope.current_user.is_superuser and store.id not in scope.allowed_store_ids():
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前用户数据范围不足",
        )
    if body.code and body.code != store.code:
        existing = get_store_by_code(session=session, code=body.code)
        if existing:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="STORE_CODE_EXISTS",
                message="门店编码已存在",
            )
    updated = update_store(
        session=session,
        store=store,
        data=body.model_dump(exclude_unset=True),
    )
    return success_response(
        request,
        data=updated.model_dump(),
        message="更新门店成功",
    )


@router.delete(
    "/{store_id}",
    summary="删除门店",
    dependencies=[Depends(require_permissions("org.store.delete"))],
    response_model=ApiResponse[None],
)
def delete_store_route(
    request: Request,
    session: SessionDep,
    store_id: uuid.UUID,
    scope: DataScopeDep,
):
    store = get_store_by_id(session=session, store_id=store_id)
    if not store:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="STORE_NOT_FOUND",
            message="门店不存在",
        )
    current_store_id = scope.resolve_current_store_id(request=request)
    if current_store_id and store.id != current_store_id:
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前门店上下文不允许删除其他门店",
        )
    if not scope.current_user.is_superuser and store.id not in scope.allowed_store_ids():
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前用户数据范围不足",
        )
    refs = check_store_deletion_references(session=session, store_id=store.id)
    if refs.in_use:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="STORE_IN_USE",
            message="门店正在使用中，暂不允许删除",
        )
    if refs.has_history:
        updated = update_store(
            session=session,
            store=store,
            data={"status": "DISABLED"},
        )
        return success_response(
            request,
            data=None,
            message=f"门店已停用：{updated.name}",
        )
    delete_store(session=session, store=store)
    return success_response(
        request,
        data=None,
        message="删除门店成功",
    )
