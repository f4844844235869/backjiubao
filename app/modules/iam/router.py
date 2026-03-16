import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlmodel import delete, select

from app.api.deps import CurrentUser, DataScopeDep, SessionDep, require_permissions
from app.core.response import ApiResponse, raise_api_error, success_response
from app.models import User
from app.modules.iam import service as iam_service
from app.modules.iam.models import (
    DataScopePublic,
    Permission,
    PermissionBase,
    PermissionPublic,
    Role,
    RoleBase,
    RoleGrant,
    RoleGrantRolePublic,
    RoleManageUpdate,
    RolePermission,
    RolePublic,
    UserAuthorizationSummary,
    UserDataScope,
    UserDataScopeAssign,
    UserRoleAssign,
    UserStoreRole,
)
from app.modules.iam.service import (
    ensure_creator_role_grant,
    ensure_self_role_grant,
    list_grantee_roles_for_role,
    list_role_permissions,
    list_visible_role_ids_for_user,
    list_visible_roles_for_user,
    replace_role_grants,
    replace_role_permissions,
    replace_user_data_scopes,
    replace_user_store_roles,
)
from app.modules.notification.service import create_notification
from app.modules.org.models import OrgNode, UserOrgBinding
from app.modules.org.service import get_user_binding_in_store

router = APIRouter(prefix="/iam", tags=["IAM"])


def _resolve_effective_store_id(
    *,
    request: Request,
    scope: DataScopeDep | None,
    current_user: CurrentUser,
) -> uuid.UUID | None:
    if scope is not None:
        current_store_id = scope.resolve_current_store_id(request=request)
    else:
        raw_store_id = request.headers.get("X-Current-Store-Id") or request.query_params.get(
            "current_store_id"
        )
        if raw_store_id:
            try:
                current_store_id = uuid.UUID(str(raw_store_id))
            except ValueError:
                raise_api_error(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code="VALIDATION_ERROR",
                    message="current_store_id 不是合法的 UUID",
                )
        else:
            current_store_id = None
    return current_store_id or current_user.primary_store_id


def _build_role_public(*, session: SessionDep, role: Role) -> RolePublic:
    permissions = list_role_permissions(session=session, role_id=role.id)
    grantable_roles = list_grantee_roles_for_role(session=session, role_id=role.id)
    grantable_payload = [
        RoleGrantRolePublic(id=item.id, code=item.code, name=item.name)
        for item in grantable_roles
    ]
    return RolePublic(
        id=role.id,
        code=role.code,
        name=role.name,
        status=role.status,
        created_by_user_id=role.created_by_user_id,
        created_at=role.created_at,
        permission_ids=[item.id for item in permissions],
        permissions=[
            PermissionPublic.model_validate(item)
            for item in permissions
        ],
        grantable_role_ids=[item.id for item in grantable_roles],
        grantable_roles=grantable_payload,
    )


def _ensure_user_matches_current_store(
    *,
    session: SessionDep,
    user: User,
    current_store_id: uuid.UUID | None,
    message: str,
) -> None:
    if current_store_id is None:
        return
    if user.primary_store_id == current_store_id:
        return
    if get_user_binding_in_store(
        session=session,
        user_id=user.id,
        store_id=current_store_id,
    ):
        return
    if session.exec(
        select(UserStoreRole)
        .where(UserStoreRole.user_id == user.id)
        .where(UserStoreRole.store_id == current_store_id)
    ).first():
        return
    data_scopes = session.exec(
        select(UserDataScope).where(UserDataScope.user_id == user.id)
    ).all()
    for item in data_scopes:
        if item.scope_type == "ALL":
            return
        if item.scope_type == "STORE" and item.store_id == current_store_id:
            return
        if item.scope_type == "DEPARTMENT" and item.org_node_id:
            org_node = session.get(OrgNode, item.org_node_id)
            if org_node and org_node.store_id == current_store_id:
                return
    raise_api_error(
        status_code=status.HTTP_403_FORBIDDEN,
        code="DATA_SCOPE_DENIED",
        message=message,
    )


def _ensure_user_in_scope(*, scope: DataScopeDep, user: User) -> None:
    if scope.current_user.is_superuser:
        return
    if scope.allows_user_record(user=user):
        return
    raise_api_error(
        status_code=status.HTTP_403_FORBIDDEN,
        code="DATA_SCOPE_DENIED",
        message="当前用户数据范围不足",
    )


def _ensure_permissions_assignable(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    permission_ids: list[uuid.UUID],
    store_id: uuid.UUID | None,
) -> None:
    if current_user.is_superuser or not permission_ids:
        return
    current_permission_codes = {
        item.code
        for item in iam_service.list_user_permissions(
            session=session, user_id=current_user.id, store_id=store_id
        )
    }
    permissions = session.exec(
        select(Permission).where(Permission.id.in_(permission_ids))
    ).all()
    missing_codes = [
        item.code for item in permissions if item.code not in current_permission_codes
    ]
    if missing_codes:
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="AUTH_GRANT_DENIED",
            message=f"不可分配超出自身权限范围的权限：{', '.join(missing_codes)}",
        )


def _ensure_roles_assignable(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    roles: list[Role],
    store_id: uuid.UUID | None,
) -> None:
    if current_user.is_superuser or not roles:
        return
    visible_role_ids = list_visible_role_ids_for_user(
        session=session,
        user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        store_id=store_id,
    )
    unauthorized_roles = [role.name for role in roles if role.id not in visible_role_ids]
    if unauthorized_roles:
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="AUTH_GRANT_DENIED",
            message=f"不可分配未授权角色：{', '.join(unauthorized_roles)}",
        )
    current_permission_codes = {
        item.code
        for item in iam_service.list_user_permissions(
            session=session, user_id=current_user.id, store_id=store_id
        )
    }
    exceeded_codes: set[str] = set()
    for role in roles:
        for permission in list_role_permissions(session=session, role_id=role.id):
            if permission.code not in current_permission_codes:
                exceeded_codes.add(permission.code)
    if exceeded_codes:
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="AUTH_GRANT_DENIED",
            message=(
                "不可分配超出自身权限范围的角色，对应超出权限为："
                f"{', '.join(sorted(exceeded_codes))}"
            ),
        )


def _ensure_scopes_assignable(
    *,
    scope: DataScopeDep,
    scopes: list[UserDataScope],
) -> None:
    if scope.current_user.is_superuser:
        return
    for item in scopes:
        if scope.allows(
            store_id=item.store_id,
            org_node_id=item.org_node_id,
            user_id=scope.current_user.id if item.scope_type == "SELF" else None,
        ):
            continue
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="AUTH_GRANT_DENIED",
            message="不可分配超出自身数据范围的授权范围",
        )


@router.get(
    "/roles",
    summary="获取角色列表",
    dependencies=[Depends(require_permissions("iam.role.read"))],
    response_model=ApiResponse[list[RolePublic]],
)
def read_roles(request: Request, session: SessionDep, current_user: CurrentUser):
    current_store_id = _resolve_effective_store_id(
        request=request,
        scope=None,
        current_user=current_user,
    )
    if current_user.is_superuser:
        roles = session.exec(select(Role).order_by(Role.created_at.desc())).all()
    else:
        roles = list_visible_roles_for_user(
            session=session,
            user_id=current_user.id,
            is_superuser=current_user.is_superuser,
            store_id=current_store_id,
        )
    return success_response(
        request,
        data=[_build_role_public(session=session, role=role).model_dump() for role in roles],
        message="获取角色列表成功",
    )


@router.post(
    "/roles",
    summary="创建角色",
    dependencies=[Depends(require_permissions("iam.role.create"))],
    response_model=ApiResponse[RolePublic],
)
def create_role(
    request: Request,
    session: SessionDep,
    body: RoleBase,
    current_user: CurrentUser,
):
    existing = session.exec(select(Role).where(Role.code == body.code)).first()
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="ROLE_CODE_EXISTS",
            message="角色编码已存在",
        )
    role = Role.model_validate(body, update={"created_by_user_id": current_user.id})
    session.add(role)
    session.commit()
    session.refresh(role)
    ensure_self_role_grant(session=session, role_id=role.id)
    ensure_creator_role_grant(
        session=session,
        grantor_user_id=current_user.id,
        grantee_role_id=role.id,
    )
    return success_response(
        request,
        data=_build_role_public(session=session, role=role).model_dump(),
        message="创建角色成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.put(
    "/roles/{role_id}",
    summary="更新角色",
    dependencies=[Depends(require_permissions("iam.role.update"))],
    response_model=ApiResponse[RolePublic],
)
def update_role(
    request: Request,
    session: SessionDep,
    role_id: uuid.UUID,
    body: RoleManageUpdate,
    current_user: CurrentUser,
):
    current_store_id = _resolve_effective_store_id(
        request=request,
        scope=None,
        current_user=current_user,
    )
    role = session.get(Role, role_id)
    if not role:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ROLE_NOT_FOUND",
            message="角色不存在",
        )
    if body.code and body.code != role.code:
        existing = session.exec(select(Role).where(Role.code == body.code)).first()
        if existing:
            raise_api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="ROLE_CODE_EXISTS",
                message="角色编码已存在",
            )
        role.code = body.code
    if body.name is not None:
        role.name = body.name
    if body.status is not None:
        role.status = body.status
    if body.permission_ids is not None:
        _ensure_permissions_assignable(
            session=session,
            current_user=current_user,
            permission_ids=body.permission_ids,
            store_id=current_store_id,
        )
        permissions = (
            list(
                session.exec(
                    select(Permission).where(Permission.id.in_(body.permission_ids))
                ).all()
            )
            if body.permission_ids
            else []
        )
        if len(permissions) != len(set(body.permission_ids)):
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="PERMISSION_NOT_FOUND",
                message="存在未找到的权限",
            )
        replace_role_permissions(
            session=session,
            role_id=role_id,
            permission_ids=body.permission_ids,
        )
    if body.grantable_role_ids is not None:
        if not current_user.is_superuser:
            raise_api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code="AUTH_PERMISSION_DENIED",
                message="当前用户无权配置角色授权边界",
            )
        grant_roles = (
            list(
                session.exec(
                    select(Role).where(Role.id.in_(body.grantable_role_ids))
                ).all()
            )
            if body.grantable_role_ids
            else []
        )
        if len(grant_roles) != len(set(body.grantable_role_ids)):
            raise_api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="ROLE_NOT_FOUND",
                message="存在未找到的角色",
            )
        replace_role_grants(
            session=session,
            grantor_role_id=role_id,
            grantee_role_ids=body.grantable_role_ids,
        )
    session.add(role)
    session.commit()
    session.refresh(role)
    return success_response(
        request,
        data=_build_role_public(session=session, role=role).model_dump(),
        message="更新角色成功",
    )


@router.delete(
    "/roles/{role_id}",
    summary="删除角色",
    dependencies=[Depends(require_permissions("iam.role.delete"))],
    response_model=ApiResponse[None],
)
def delete_role(request: Request, session: SessionDep, role_id: uuid.UUID):
    role = session.get(Role, role_id)
    if not role:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ROLE_NOT_FOUND",
            message="角色不存在",
        )
    if role.code == "admin":
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="ROLE_DELETE_FORBIDDEN",
            message="系统管理员角色不允许删除",
        )
    role_permissions = session.exec(
        select(RolePermission).where(RolePermission.role_id == role_id)
    ).all()
    for item in role_permissions:
        session.delete(item)
    user_roles = session.exec(
        select(UserStoreRole).where(UserStoreRole.role_id == role_id)
    ).all()
    for item in user_roles:
        session.delete(item)
    session.exec(
        delete(RoleGrant).where(
            (RoleGrant.grantor_role_id == role_id)
            | (RoleGrant.grantee_role_id == role_id)
        )
    )
    session.delete(role)
    session.commit()
    return success_response(
        request,
        data=None,
        message="删除角色成功",
    )


@router.get(
    "/permissions",
    summary="获取权限列表",
    dependencies=[Depends(require_permissions("iam.permission.read"))],
    response_model=ApiResponse[list[PermissionPublic]],
)
def read_permissions(
    request: Request,
    session: SessionDep,
    current_user: CurrentUser,
):
    current_store_id = _resolve_effective_store_id(
        request=request,
        scope=None,
        current_user=current_user,
    )
    if current_user.is_superuser:
        permissions = session.exec(
            select(Permission).order_by(Permission.created_at.desc())
        ).all()
    else:
        permissions = iam_service.list_user_permissions(
            session=session,
            user_id=current_user.id,
            store_id=current_store_id,
        )
    return success_response(
        request,
        data=[
            PermissionPublic.model_validate(permission).model_dump()
            for permission in permissions
        ],
        message="获取权限列表成功",
    )


@router.get(
    "/users/{user_id}/authorization-summary",
    summary="获取用户授权摘要",
    dependencies=[Depends(require_permissions("iam.user.read"))],
    response_model=ApiResponse[UserAuthorizationSummary],
)
def read_user_authorization_summary(
    request: Request,
    session: SessionDep,
    user_id: uuid.UUID,
    scope: DataScopeDep,
):
    user = session.get(User, user_id)
    if not user:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="用户不存在",
        )
    current_store_id = scope.resolve_current_store_id(request=request)
    effective_store_id = current_store_id or user.primary_store_id
    _ensure_user_matches_current_store(
        session=session,
        user=user,
        current_store_id=current_store_id,
        message="当前门店上下文不匹配目标用户",
    )
    _ensure_user_in_scope(scope=scope, user=user)
    roles = iam_service.list_user_roles(
        session=session, user_id=user_id, store_id=effective_store_id
    )
    permissions = iam_service.list_user_permissions(
        session=session, user_id=user_id, store_id=effective_store_id
    )
    data_scopes = iam_service.list_user_data_scopes(session=session, user_id=user_id)
    summary = UserAuthorizationSummary(
        **user.model_dump(),
        roles=[RolePublic.model_validate(item) for item in roles],
        permissions=[PermissionPublic.model_validate(item) for item in permissions],
        data_scopes=[
            DataScopePublic(
                scope_type=item.scope_type,
                store_id=item.store_id,
                org_node_id=item.org_node_id,
            )
            for item in data_scopes
        ],
    )
    return success_response(
        request,
        data=summary.model_dump(mode="json"),
        message="获取用户授权摘要成功",
    )


@router.post(
    "/permissions",
    summary="创建权限",
    dependencies=[Depends(require_permissions("iam.permission.create"))],
    response_model=ApiResponse[PermissionPublic],
)
def create_permission(request: Request, session: SessionDep, body: PermissionBase):
    existing = session.exec(select(Permission).where(Permission.code == body.code)).first()
    if existing:
        raise_api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="PERMISSION_CODE_EXISTS",
            message="权限编码已存在",
        )
    permission = Permission.model_validate(body)
    session.add(permission)
    session.commit()
    session.refresh(permission)
    return success_response(
        request,
        data=PermissionPublic.model_validate(permission).model_dump(),
        message="创建权限成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.put(
    "/users/{user_id}/stores/{store_id}/roles",
    summary="分配用户角色",
    include_in_schema=False,
    dependencies=[Depends(require_permissions("iam.user.assign_role"))],
    response_model=ApiResponse[list[RolePublic]],
)
def assign_user_roles(
    request: Request,
    session: SessionDep,
    user_id: uuid.UUID,
    store_id: uuid.UUID,
    body: UserRoleAssign,
    current_user: CurrentUser,
    scope: DataScopeDep,
):
    user = session.get(User, user_id)
    if not user:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="用户不存在",
        )
    current_store_id = scope.resolve_current_store_id(request=request)
    if current_store_id and current_store_id != store_id:
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="DATA_SCOPE_DENIED",
            message="当前门店上下文不允许修改其他门店角色",
        )
    _ensure_user_in_scope(scope=scope, user=user)
    roles = (
        list(session.exec(select(Role).where(Role.id.in_(body.role_ids))).all())
        if body.role_ids
        else []
    )
    if len(roles) != len(set(body.role_ids)):
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ROLE_NOT_FOUND",
            message="存在未找到的角色",
        )
    _ensure_roles_assignable(
        session=session,
        current_user=current_user,
        roles=roles,
        store_id=store_id,
    )
    bindings = replace_user_store_roles(
        session=session,
        user_id=user_id,
        store_id=store_id,
        role_ids=body.role_ids,
    )
    role_ids = [binding.role_id for binding in bindings]
    saved_roles = (
        session.exec(select(Role).where(Role.id.in_(role_ids))).all() if role_ids else []
    )
    role_names = "、".join(role.name for role in saved_roles) if saved_roles else "无角色"
    create_notification(
        session=session,
        user_id=user_id,
        notification_type="USER_ROLE_CHANGED",
        title="角色已更新",
        content=f"你在当前门店的角色已更新为：{role_names}。",
    )
    session.commit()
    return success_response(
        request,
        data=[
            _build_role_public(session=session, role=role).model_dump()
            for role in saved_roles
        ],
        message="分配用户角色成功",
    )


@router.put(
    "/users/{user_id}/roles",
    summary="按当前门店分配用户角色",
    dependencies=[Depends(require_permissions("iam.user.assign_role"))],
    response_model=ApiResponse[list[RolePublic]],
)
def assign_user_roles_compat(
    request: Request,
    session: SessionDep,
    user_id: uuid.UUID,
    body: UserRoleAssign,
    current_user: CurrentUser,
    scope: DataScopeDep,
):
    target_user = session.get(User, user_id)
    if not target_user:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="用户不存在",
        )
    store_id = _resolve_effective_store_id(
        request=request,
        scope=scope,
        current_user=current_user,
    )
    if store_id is None:
        store_id = target_user.primary_store_id
    if store_id is None:
        first_binding = session.exec(
            select(OrgNode.store_id)
            .join(UserOrgBinding, UserOrgBinding.org_node_id == OrgNode.id)
            .where(UserOrgBinding.user_id == user_id)
            .order_by(UserOrgBinding.created_at.asc())
        ).first()
        store_id = first_binding
    if store_id is None:
        raise_api_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="CURRENT_STORE_REQUIRED",
            message="缺少当前门店上下文，请通过请求头 X-Current-Store-Id 传入门店 ID",
        )
    return assign_user_roles(
        request=request,
        session=session,
        user_id=user_id,
        store_id=store_id,
        body=body,
        current_user=current_user,
        scope=scope,
    )


@router.put(
    "/users/{user_id}/data-scopes",
    summary="分配用户数据范围",
    dependencies=[Depends(require_permissions("iam.user.assign_scope"))],
    response_model=ApiResponse[list[DataScopePublic]],
)
def assign_user_data_scopes(
    request: Request,
    session: SessionDep,
    user_id: uuid.UUID,
    body: UserDataScopeAssign,
    scope: DataScopeDep,
):
    user = session.get(User, user_id)
    if not user:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="用户不存在",
        )
    current_store_id = scope.resolve_current_store_id(request=request)
    _ensure_user_in_scope(scope=scope, user=user)
    scopes = [
        UserDataScope(
            user_id=user_id,
            scope_type=item.scope_type,
            store_id=item.store_id,
            org_node_id=item.org_node_id,
        )
        for item in body.scopes
    ]
    if current_store_id:
        org_node_ids = {item.org_node_id for item in scopes if item.org_node_id}
        org_nodes = {
            node.id: node
            for node in (
                session.exec(select(OrgNode).where(OrgNode.id.in_(org_node_ids))).all()
                if org_node_ids
                else []
            )
        }
        for item in scopes:
            item_store_id = item.store_id
            if item.org_node_id and item.org_node_id in org_nodes:
                item_store_id = org_nodes[item.org_node_id].store_id
            if item.scope_type in {"STORE", "DEPARTMENT"} and item_store_id != current_store_id:
                raise_api_error(
                    status_code=status.HTTP_403_FORBIDDEN,
                    code="DATA_SCOPE_DENIED",
                    message="当前门店上下文不允许分配其他门店数据范围",
                )
    _ensure_scopes_assignable(scope=scope, scopes=scopes)
    saved = replace_user_data_scopes(session=session, user_id=user_id, scopes=scopes)
    create_notification(
        session=session,
        user_id=user_id,
        notification_type="USER_SCOPE_CHANGED",
        title="数据范围已更新",
        content="你的数据访问范围已更新，请刷新页面查看最新权限。",
    )
    session.commit()
    return success_response(
        request,
        data=[
            DataScopePublic(
                scope_type=item.scope_type,
                store_id=item.store_id,
                org_node_id=item.org_node_id,
            ).model_dump()
            for item in saved
        ],
        message="分配用户数据范围成功",
    )
