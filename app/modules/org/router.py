import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlmodel import select

from app.api.deps import (
    CurrentUser,
    DataScopeDep,
    SessionDep,
    require_permissions,
)
from app.core.response import ApiResponse, raise_api_error, success_response
from app.models import User
from app.modules.employee.service import update_active_employment_record_assignment
from app.modules.notification.service import create_notification
from app.modules.org.models import (
    OrgNode,
    OrgNodeCreate,
    OrgNodeMembersResponse,
    OrgNodePublic,
    OrgNodeUpdate,
    UserOrgBinding,
    UserOrgBindingCreate,
    UserOrgBindingPublic,
    UserOrgBindingUpdate,
)
from app.modules.org.service import (
    check_org_node_deletion_references,
    clear_primary_binding,
    create_org_node,
    delete_org_node,
    get_sibling_prefix_conflict,
    list_org_node_members,
    list_org_nodes,
    list_user_org_bindings,
    normalize_org_prefix,
    sync_user_primary_org,
    update_org_node,
)

router = APIRouter(prefix="/org", tags=["Organization"])


@router.get(
    "/nodes/{node_id}/members",
    summary="获取组织下级成员列表",
    dependencies=[Depends(require_permissions("employee.read"))],
    response_model=ApiResponse[OrgNodeMembersResponse],
)
def read_org_node_members_route(
    request: Request,
    session: SessionDep,
    node_id: uuid.UUID,
    scope: DataScopeDep,
    include_descendants: bool = True,
):
    node = session.get(OrgNode, node_id)
    if not node:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ORG_NODE_NOT_FOUND",
            message="组织节点不存在",
        )
    current_store_id = scope.resolve_current_store_id(request=request)
    if current_store_id and node.store_id != current_store_id:
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前门店上下文不允许查看其他门店成员",
        )
    if not scope.current_user.is_superuser and not scope.allows(
        store_id=node.store_id, org_node_id=node.id
    ):
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前用户数据范围不足",
        )
    org_nodes, members = list_org_node_members(
        session=session,
        node=node,
        include_descendants=include_descendants,
    )
    return success_response(
        request,
        data={
            "org_nodes": [item.model_dump(mode="json") for item in org_nodes],
            "members": [item.model_dump(mode="json") for item in members],
        },
        message="获取组织成员成功",
    )


@router.get(
    "/nodes",
    summary="获取组织节点列表",
    dependencies=[Depends(require_permissions("org.node.read"))],
    response_model=ApiResponse[list[OrgNodePublic]],
)
def read_org_nodes_route(
    request: Request,
    session: SessionDep,
    scope: DataScopeDep,
    store_id: uuid.UUID | None = None,
):
    current_store_id = scope.resolve_current_store_id(request=request)
    nodes = list_org_nodes(session=session, store_id=store_id)
    if not scope.current_user.is_superuser:
        if store_id and store_id not in scope.allowed_store_ids():
            raise_api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code="DATA_SCOPE_DENIED",
                message="当前用户数据范围不足",
            )
        nodes = [
            node
            for node in nodes
            if scope.allows(store_id=node.store_id, org_node_id=node.id)
        ]
    if current_store_id:
        nodes = [node for node in nodes if node.store_id == current_store_id]
    return success_response(
        request,
        data=[node.model_dump() for node in nodes],
        message="获取组织节点成功",
    )


@router.post(
    "/nodes",
    summary="创建组织节点",
    dependencies=[Depends(require_permissions("org.node.create"))],
    response_model=ApiResponse[OrgNodePublic],
)
def create_org_node_route(
    request: Request, session: SessionDep, body: OrgNodeCreate, scope: DataScopeDep
):
    if not scope.current_user.is_superuser and not scope.allows(store_id=body.store_id):
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前用户数据范围不足",
        )
    try:
        body.prefix = normalize_org_prefix(body.prefix)
    except ValueError:
        raise_api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="ORG_PREFIX_INVALID",
            message="组织前缀只能包含字母和数字",
        )
    parent = None
    if body.parent_id:
        parent = session.get(OrgNode, body.parent_id)
        if not parent:
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="ORG_PARENT_NOT_FOUND",
                message="父组织节点不存在",
            )
        if parent.store_id != body.store_id:
            raise_api_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="ORG_PARENT_STORE_MISMATCH",
                message="父节点与当前门店不匹配",
            )
    existing_prefix_node = get_sibling_prefix_conflict(
        session=session,
        store_id=body.store_id,
        parent_id=body.parent_id,
        prefix=body.prefix,
    )
    if existing_prefix_node:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="ORG_PREFIX_EXISTS",
            message="同级组织前缀已存在",
        )

    node = create_org_node(session=session, body=body, parent=parent)
    return success_response(
        request,
        data=node.model_dump(),
        message="创建组织节点成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/nodes/{node_id}",
    summary="更新组织节点",
    dependencies=[Depends(require_permissions("org.node.update"))],
    response_model=ApiResponse[OrgNodePublic],
)
def update_org_node_route(
    request: Request,
    session: SessionDep,
    node_id: uuid.UUID,
    body: OrgNodeUpdate,
    scope: DataScopeDep,
):
    node = session.get(OrgNode, node_id)
    if not node:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ORG_NODE_NOT_FOUND",
            message="组织节点不存在",
        )
    current_store_id = scope.resolve_current_store_id(request=request)
    if current_store_id and node.store_id != current_store_id:
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前门店上下文不允许修改其他门店组织",
        )
    if not scope.current_user.is_superuser and not scope.allows(
        store_id=node.store_id, org_node_id=node.id
    ):
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前用户数据范围不足",
        )
    update_data = body.model_dump(exclude_unset=True)
    if "prefix" in update_data and update_data["prefix"] is not None:
        try:
            update_data["prefix"] = normalize_org_prefix(update_data["prefix"])
        except ValueError:
            raise_api_error(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="ORG_PREFIX_INVALID",
                message="组织前缀只能包含字母和数字",
            )
        existing_prefix_node = get_sibling_prefix_conflict(
            session=session,
            store_id=node.store_id,
            parent_id=node.parent_id,
            prefix=update_data["prefix"],
            exclude_node_id=node.id,
        )
        if existing_prefix_node:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="ORG_PREFIX_EXISTS",
                message="同级组织前缀已存在",
            )
    updated = update_org_node(
        session=session,
        node=node,
        data=update_data,
    )
    return success_response(
        request,
        data=updated.model_dump(),
        message="更新组织节点成功",
    )


@router.delete(
    "/nodes/{node_id}",
    summary="删除组织节点",
    dependencies=[Depends(require_permissions("org.node.delete"))],
    response_model=ApiResponse[None],
)
def delete_org_node_route(
    request: Request,
    session: SessionDep,
    node_id: uuid.UUID,
    scope: DataScopeDep,
):
    node = session.get(OrgNode, node_id)
    if not node:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ORG_NODE_NOT_FOUND",
            message="组织节点不存在",
        )
    current_store_id = scope.resolve_current_store_id(request=request)
    if current_store_id and node.store_id != current_store_id:
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前门店上下文不允许删除其他门店组织",
        )
    if not scope.current_user.is_superuser and not scope.allows(
        store_id=node.store_id, org_node_id=node.id
    ):
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前用户数据范围不足",
        )
    refs = check_org_node_deletion_references(session=session, node_id=node.id)
    if refs.in_use or refs.has_any_children:
        message = "组织节点正在使用中，暂不允许删除"
        if refs.has_any_children:
            message = "组织节点存在子节点，暂不允许删除"
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="ORG_NODE_IN_USE",
            message=message,
        )
    if refs.has_history:
        updated = update_org_node(
            session=session,
            node=node,
            data={"is_active": False},
        )
        return success_response(
            request,
            data=None,
            message=f"组织节点已停用：{updated.name}",
        )
    delete_org_node(session=session, node=node)
    return success_response(
        request,
        data=None,
        message="删除组织节点成功",
    )


@router.get(
    "/bindings",
    summary="获取用户组织绑定列表",
    dependencies=[Depends(require_permissions("org.binding.read"))],
    response_model=ApiResponse[list[UserOrgBindingPublic]],
)
def read_user_org_bindings_route(
    request: Request,
    session: SessionDep,
    scope: DataScopeDep,
    user_id: uuid.UUID | None = None,
):
    current_store_id = scope.resolve_current_store_id(request=request)
    bindings = list_user_org_bindings(session=session, user_id=user_id)
    if not scope.current_user.is_superuser:
        org_node_ids = {binding.org_node_id for binding in bindings}
        org_nodes = {
            node.id: node
            for node in session.exec(select(OrgNode).where(OrgNode.id.in_(org_node_ids))).all()
        }
        bindings = [
            binding
            for binding in bindings
            if (
                binding.user_id == scope.current_user.id
                or (
                    binding.org_node_id in org_nodes
                    and scope.allows(
                        store_id=org_nodes[binding.org_node_id].store_id,
                        org_node_id=binding.org_node_id,
                    )
                )
            )
        ]
    if current_store_id:
        org_nodes_by_id = {
            node.id: node
            for node in session.exec(
                select(OrgNode).where(OrgNode.id.in_({binding.org_node_id for binding in bindings}))
            ).all()
        }
        bindings = [
            binding
            for binding in bindings
            if binding.org_node_id in org_nodes_by_id
            and org_nodes_by_id[binding.org_node_id].store_id == current_store_id
        ]
    return success_response(
        request,
        data=[binding.model_dump() for binding in bindings],
        message="获取用户组织绑定成功",
    )


@router.post(
    "/bindings",
    summary="创建用户组织绑定",
    dependencies=[Depends(require_permissions("org.binding.create"))],
    response_model=ApiResponse[UserOrgBindingPublic],
)
def create_user_org_binding_route(
    request: Request,
    session: SessionDep,
    body: UserOrgBindingCreate,
    current_user: CurrentUser,
    scope: DataScopeDep,
):
    user = session.get(User, body.user_id)
    if not user:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="用户不存在",
        )
    org_node = session.get(OrgNode, body.org_node_id)
    if not org_node:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ORG_NODE_NOT_FOUND",
            message="组织节点不存在",
        )
    current_store_id = scope.resolve_current_store_id(request=request)
    if current_store_id and org_node.store_id != current_store_id:
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前门店上下文不允许绑定其他门店组织",
        )
    if not current_user.is_superuser:
        if not scope.allows_user_record(user=user):
            raise_api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code="DATA_SCOPE_DENIED",
                message="当前用户数据范围不足",
            )
        if not scope.allows(store_id=org_node.store_id, org_node_id=org_node.id):
            raise_api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code="DATA_SCOPE_DENIED",
                message="当前用户数据范围不足",
            )

    if body.is_primary:
        clear_primary_binding(session=session, user_id=body.user_id)
        sync_user_primary_org(session=session, user=user, org_node=org_node)

    binding = UserOrgBinding.model_validate(body)
    session.add(binding)
    create_notification(
        session=session,
        user_id=binding.user_id,
        notification_type="ORG_BINDING_CREATED",
        title="组织归属已新增",
        content=f"你已新增组织归属：{org_node.name}。",
    )
    session.commit()
    session.refresh(binding)
    return success_response(
        request,
        data=binding.model_dump(),
        message="创建用户组织绑定成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch(
    "/bindings/{binding_id}",
    summary="更新用户组织绑定",
    dependencies=[Depends(require_permissions("org.binding.update"))],
    response_model=ApiResponse[UserOrgBindingPublic],
)
def update_user_org_binding_route(
    request: Request,
    session: SessionDep,
    binding_id: uuid.UUID,
    body: UserOrgBindingUpdate,
    current_user: CurrentUser,
    scope: DataScopeDep,
):
    binding = session.get(UserOrgBinding, binding_id)
    if not binding:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ORG_BINDING_NOT_FOUND",
            message="组织绑定不存在",
        )
    user = session.get(User, binding.user_id)
    if not user:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="用户不存在",
        )
    org_node = session.get(OrgNode, binding.org_node_id)
    if not org_node:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ORG_NODE_NOT_FOUND",
            message="组织节点不存在",
        )
    target_org_node = org_node
    if body.org_node_id and body.org_node_id != binding.org_node_id:
        target_org_node = session.get(OrgNode, body.org_node_id)
        if not target_org_node:
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="ORG_NODE_NOT_FOUND",
                message="目标组织节点不存在",
            )
        if target_org_node.store_id != org_node.store_id:
            raise_api_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="ORG_BINDING_STORE_MISMATCH",
                message="组织变更仅支持同门店内调整",
            )
    current_store_id = scope.resolve_current_store_id(request=request)
    if current_store_id and target_org_node.store_id != current_store_id:
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前门店上下文不允许修改其他门店组织绑定",
        )
    if not current_user.is_superuser:
        if not scope.allows_user_record(user=user):
            raise_api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code="DATA_SCOPE_DENIED",
                message="当前用户数据范围不足",
            )
        if not scope.allows(
            store_id=target_org_node.store_id, org_node_id=target_org_node.id
        ):
            raise_api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code="DATA_SCOPE_DENIED",
                message="当前用户数据范围不足",
            )

    if body.org_node_id is not None:
        binding.org_node_id = target_org_node.id

    if body.position_name is not None:
        binding.position_name = body.position_name

    if body.is_primary is True and not binding.is_primary:
        clear_primary_binding(session=session, user_id=binding.user_id)
        binding.is_primary = True
        sync_user_primary_org(session=session, user=user, org_node=target_org_node)
    elif body.is_primary is False:
        # 避免出现没有主归属的状态，这里不允许直接取消主归属。
        if binding.is_primary:
            raise_api_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="ORG_PRIMARY_BINDING_REQUIRED",
                message="当前主归属不能直接取消，请先指定新的主归属",
            )
        binding.is_primary = False

    session.add(binding)
    notification_content = f"你的组织归属已更新为：{target_org_node.name}。"
    if body.position_name is not None:
        notification_content = (
            f"你的组织/岗位信息已更新，当前组织：{target_org_node.name}，"
            f"岗位：{binding.position_name or '未设置'}。"
        )
    create_notification(
        session=session,
        user_id=binding.user_id,
        notification_type="ORG_BINDING_UPDATED",
        title="组织归属已更新",
        content=notification_content,
    )
    session.commit()
    session.refresh(binding)

    if binding.is_primary and body.org_node_id is not None:
        sync_user_primary_org(session=session, user=user, org_node=target_org_node)
        session.commit()
        session.refresh(binding)

    if body.position_name is not None or body.org_node_id is not None:
        update_active_employment_record_assignment(
            session=session,
            user_id=binding.user_id,
            org_node_id=target_org_node.id if body.org_node_id is not None else None,
            position_name=binding.position_name if body.position_name is not None else None,
        )
        session.refresh(binding)

    return success_response(
        request,
        data=binding.model_dump(),
        message="更新用户组织绑定成功",
    )
