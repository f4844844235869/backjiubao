import uuid
from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session, select

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.core.response import AppException, raise_api_error
from app.models import (
    AccessibleStorePublic,
    CurrentUserProfile,
    DataScopePublic,
    Store,
    StoreMembershipPublic,
    TokenPayload,
    User,
    UserDataScope,
)
from app.modules.iam import service as iam_service
from app.modules.org.models import OrgNode, UserOrgBinding
from app.modules.org.service import get_user_binding_in_store

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/backend/password-login",
    auto_error=False,
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str | None, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    if not token:
        raise_api_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTH_INVALID_TOKEN",
            message="未登录或登录状态已过期",
        )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise_api_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTH_INVALID_TOKEN",
            message="登录状态无效或已过期",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise_api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="用户不存在",
        )
    if not user.is_active or user.status != "ACTIVE":
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="USER_DISABLED",
            message="当前用户已被禁用",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="AUTH_PERMISSION_DENIED",
            message="当前用户权限不足",
        )
    return current_user


class DataScopeContext:
    def __init__(
        self,
        current_user: User,
        data_scopes: list[UserDataScope],
        session: Session,
    ) -> None:
        self.current_user = current_user
        self.data_scopes = data_scopes
        self.session = session
        self._expanded_org_node_ids: set[uuid.UUID] | None = None

    def allows(
        self,
        *,
        store_id: uuid.UUID | None = None,
        org_node_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
    ) -> bool:
        if self.current_user.is_superuser:
            return True
        if not self.data_scopes:
            return user_id == self.current_user.id if user_id else False

        for scope in self.data_scopes:
            if scope.scope_type == "ALL":
                return True
            if scope.scope_type == "SELF" and user_id == self.current_user.id:
                return True
            if scope.scope_type == "STORE" and store_id and scope.store_id == store_id:
                return True
            if (
                scope.scope_type == "DEPARTMENT"
                and org_node_id
                and org_node_id in self.expanded_org_node_ids()
            ):
                return True
        return False

    def expanded_org_node_ids(self) -> set[uuid.UUID]:
        if self.current_user.is_superuser:
            return set()
        if self._expanded_org_node_ids is not None:
            return self._expanded_org_node_ids

        scoped_org_nodes = [
            scope.org_node_id
            for scope in self.data_scopes
            if scope.scope_type == "DEPARTMENT" and scope.org_node_id
        ]
        if not scoped_org_nodes:
            self._expanded_org_node_ids = set()
            return self._expanded_org_node_ids

        scoped_nodes = self.session.exec(
            select(OrgNode).where(OrgNode.id.in_(scoped_org_nodes))
        ).all()
        all_nodes = self.session.exec(select(OrgNode)).all()
        expanded_ids: set[uuid.UUID] = set()
        for scoped_node in scoped_nodes:
            for node in all_nodes:
                if node.id == scoped_node.id or node.path.startswith(f"{scoped_node.path}/"):
                    expanded_ids.add(node.id)
        self._expanded_org_node_ids = expanded_ids
        return self._expanded_org_node_ids

    def allowed_store_ids(self) -> set[uuid.UUID]:
        if self.current_user.is_superuser:
            return set()

        store_ids: set[uuid.UUID] = set()
        include_self = False

        for scope in self.data_scopes:
            if scope.scope_type == "ALL":
                return set()
            if scope.scope_type == "STORE" and scope.store_id:
                store_ids.add(scope.store_id)
            if scope.scope_type == "SELF":
                include_self = True

        expanded_org_node_ids = self.expanded_org_node_ids()
        if expanded_org_node_ids:
            statement = select(OrgNode.store_id).where(OrgNode.id.in_(expanded_org_node_ids))
            store_ids.update(item for item in self.session.exec(statement).all())
        if include_self and self.current_user.primary_store_id:
            store_ids.add(self.current_user.primary_store_id)
        return store_ids

    def allows_user_record(self, *, user: User) -> bool:
        return self.allows(
            store_id=user.primary_store_id,
            org_node_id=user.primary_department_id,
            user_id=user.id,
        )

    def can_access_store(self, *, store_id: uuid.UUID) -> bool:
        if self.current_user.is_superuser:
            return True
        if any(scope.scope_type == "ALL" for scope in self.data_scopes):
            return True
        return store_id in self.allowed_store_ids()

    def resolve_current_store_id(self, *, request: Request) -> uuid.UUID | None:
        raw_value = request.headers.get("X-Current-Store-Id") or request.query_params.get(
            "current_store_id"
        )
        if not raw_value:
            return None
        try:
            store_id = uuid.UUID(str(raw_value))
        except ValueError as exc:
            raise AppException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="VALIDATION_ERROR",
                message="current_store_id 不是合法的 UUID",
            ) from exc
        if self.current_user.is_superuser:
            return store_id
        if store_id not in self.allowed_store_ids():
            raise_api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code="DATA_SCOPE_DENIED",
                message="当前门店上下文不在可访问范围内",
            )
        return store_id

    def applies_current_store(
        self,
        *,
        current_store_id: uuid.UUID | None,
        store_id: uuid.UUID | None,
    ) -> bool:
        if current_store_id is None:
            return True
        return store_id == current_store_id


def get_current_user_profile(
    request: Request, session: SessionDep, current_user: CurrentUser
) -> CurrentUserProfile:
    roles = iam_service.list_user_roles(session=session, user_id=current_user.id)
    permissions = iam_service.list_user_permissions(
        session=session, user_id=current_user.id
    )
    data_scopes = iam_service.list_user_data_scopes(
        session=session, user_id=current_user.id
    )
    scope = DataScopeContext(
        current_user=current_user,
        data_scopes=data_scopes,
        session=session,
    )
    current_store_id = scope.resolve_current_store_id(request=request)
    if current_store_id is None:
        current_store_id = current_user.primary_store_id
    current_org_node_id = current_user.primary_department_id
    if current_store_id and not session.get(Store, current_store_id):
        current_store_id = None
        current_org_node_id = None
    if current_store_id:
        binding = get_user_binding_in_store(
            session=session,
            user_id=current_user.id,
            store_id=current_store_id,
        )
        if binding:
            current_org_node_id = binding.org_node_id
        elif current_org_node_id is None and current_user.is_superuser:
            current_store_default_org = session.exec(
                select(OrgNode)
                .where(OrgNode.store_id == current_store_id)
                .where(OrgNode.parent_id.is_(None))
                .order_by(OrgNode.sort_order, OrgNode.created_at, OrgNode.name)
            ).first()
            if current_store_default_org:
                current_org_node_id = current_store_default_org.id
    org_bindings = session.exec(
        select(UserOrgBinding).where(UserOrgBinding.user_id == current_user.id)
    ).all()
    org_node_ids = {binding.org_node_id for binding in org_bindings}
    if current_user.primary_department_id:
        org_node_ids.add(current_user.primary_department_id)
    if current_org_node_id:
        org_node_ids.add(current_org_node_id)
    org_nodes = (
        {
            node.id: node
            for node in session.exec(select(OrgNode).where(OrgNode.id.in_(org_node_ids))).all()
        }
        if org_node_ids
        else {}
    )
    store_ids = {node.store_id for node in org_nodes.values()}
    stores = (
        {
            store.id: store
            for store in session.exec(select(Store).where(Store.id.in_(store_ids))).all()
        }
        if store_ids
        else {}
    )
    membership_by_store: dict[uuid.UUID, StoreMembershipPublic] = {}
    for binding in org_bindings:
        org_node = org_nodes.get(binding.org_node_id)
        if not org_node:
            continue
        store = stores.get(org_node.store_id)
        if not store:
            continue
        candidate = StoreMembershipPublic(
            store_id=store.id,
            store_name=store.name,
            org_node_id=org_node.id,
            org_node_name=org_node.name,
            position_name=binding.position_name,
            is_primary=binding.is_primary,
            is_current=store.id == current_store_id,
        )
        existing = membership_by_store.get(store.id)
        if existing is None or (candidate.is_primary and not existing.is_primary):
            membership_by_store[store.id] = candidate
    accessible_store_map: dict[uuid.UUID, AccessibleStorePublic] = {}
    if scope.current_user.is_superuser:
        accessible_stores = session.exec(select(Store).order_by(Store.name, Store.code)).all()
        for store in accessible_stores:
            accessible_store_map[store.id] = AccessibleStorePublic(
                store_id=store.id,
                store_name=store.name,
                is_current=store.id == current_store_id,
            )
    else:
        accessible_store_ids = set(scope.allowed_store_ids())
        accessible_store_ids.update(membership_by_store.keys())
        if current_store_id:
            accessible_store_ids.add(current_store_id)
        if accessible_store_ids:
            accessible_stores = session.exec(
                select(Store)
                .where(Store.id.in_(accessible_store_ids))
                .order_by(Store.name, Store.code)
            ).all()
            for store in accessible_stores:
                accessible_store_map[store.id] = AccessibleStorePublic(
                    store_id=store.id,
                    store_name=store.name,
                    is_current=store.id == current_store_id,
                )
    current_store_name = None
    if current_store_id:
        current_store = stores.get(current_store_id)
        if not current_store:
            current_store = session.get(Store, current_store_id)
        current_store_name = current_store.name if current_store else None
    primary_store_name = None
    if current_user.primary_store_id:
        primary_store = stores.get(current_user.primary_store_id)
        if not primary_store:
            primary_store = session.get(Store, current_user.primary_store_id)
        primary_store_name = primary_store.name if primary_store else None
    primary_department_name = None
    if current_user.primary_department_id:
        primary_department = org_nodes.get(current_user.primary_department_id)
        if not primary_department:
            primary_department = session.get(OrgNode, current_user.primary_department_id)
        primary_department_name = primary_department.name if primary_department else None
    current_org_node_name = None
    if current_org_node_id:
        current_org_node = org_nodes.get(current_org_node_id)
        if not current_org_node:
            current_org_node = session.get(OrgNode, current_org_node_id)
        current_org_node_name = current_org_node.name if current_org_node else None

    def build_scope_label(scope_item: UserDataScope) -> str:
        if scope_item.scope_type == "ALL":
            return "全部数据"
        if scope_item.scope_type == "SELF":
            return "仅本人数据"
        if scope_item.scope_type == "STORE":
            scope_store = None
            if scope_item.store_id:
                scope_store = stores.get(scope_item.store_id) or session.get(Store, scope_item.store_id)
            return f"门店：{scope_store.name}" if scope_store else "指定门店数据"
        if scope_item.scope_type == "DEPARTMENT":
            scope_org = None
            if scope_item.org_node_id:
                scope_org = org_nodes.get(scope_item.org_node_id) or session.get(
                    OrgNode, scope_item.org_node_id
                )
            return f"组织：{scope_org.name}" if scope_org else "指定组织数据"
        return scope_item.scope_type

    return CurrentUserProfile.model_validate(
        {
            **current_user.model_dump(),
            "primary_store_name": primary_store_name,
            "primary_department_name": primary_department_name,
            "current_store_id": current_store_id,
            "current_store_name": current_store_name,
            "current_org_node_id": current_org_node_id,
            "current_org_node_name": current_org_node_name,
            "roles": [role.code for role in roles],
            "role_names": [role.name for role in roles],
            "permissions": [permission.code for permission in permissions],
            "permission_names": [permission.name for permission in permissions],
            "data_scopes": [
                DataScopePublic(
                    scope_type=scope.scope_type,
                    store_id=scope.store_id,
                    org_node_id=scope.org_node_id,
                    scope_label=build_scope_label(scope),
                )
                for scope in data_scopes
            ],
            "data_scope_labels": [build_scope_label(scope) for scope in data_scopes],
            "store_memberships": [
                membership.model_dump(mode="json")
                for membership in membership_by_store.values()
            ],
            "accessible_stores": [
                store.model_dump(mode="json") for store in accessible_store_map.values()
            ],
        }
    )


CurrentUserProfileDep = Annotated[
    CurrentUserProfile, Depends(get_current_user_profile)
]


def get_data_scope_context(
    session: SessionDep, current_user: CurrentUser
) -> DataScopeContext:
    return DataScopeContext(
        current_user=current_user,
        data_scopes=iam_service.list_user_data_scopes(
            session=session, user_id=current_user.id
        ),
        session=session,
    )


DataScopeDep = Annotated[DataScopeContext, Depends(get_data_scope_context)]


def require_roles(*role_codes: str):
    def dependency(session: SessionDep, current_user: CurrentUser) -> User:
        if current_user.is_superuser:
            return current_user
        roles = iam_service.list_user_roles(session=session, user_id=current_user.id)
        current_role_codes = {role.code for role in roles}
        missing_roles = [code for code in role_codes if code not in current_role_codes]
        if missing_roles:
            raise_api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code="AUTH_ROLE_DENIED",
                message=f"缺少角色：{', '.join(missing_roles)}",
            )
        return current_user

    return dependency


def require_permissions(*permission_codes: str):
    def dependency(session: SessionDep, current_user: CurrentUser) -> User:
        if current_user.is_superuser:
            return current_user
        permissions = iam_service.list_user_permissions(
            session=session, user_id=current_user.id
        )
        current_permission_codes = {permission.code for permission in permissions}
        missing_permissions = [
            code for code in permission_codes if code not in current_permission_codes
        ]
        if missing_permissions:
            raise_api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code="AUTH_PERMISSION_DENIED",
                message=f"缺少权限：{', '.join(missing_permissions)}",
            )
        return current_user

    return dependency


def require_data_scope(
    *,
    store_param: str | None = "store_id",
    org_param: str | None = "org_node_id",
    user_param: str | None = "user_id",
):
    def dependency(request: Request, current_user: CurrentUser, scope: DataScopeDep) -> None:
        def read_uuid(param_name: str | None) -> uuid.UUID | None:
            if not param_name:
                return None
            raw_value = request.path_params.get(param_name) or request.query_params.get(
                param_name
            )
            if not raw_value:
                return None
            try:
                return uuid.UUID(str(raw_value))
            except ValueError as exc:
                raise AppException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code="VALIDATION_ERROR",
                    message=f"{param_name} 不是合法的 UUID",
                ) from exc

        store_id = read_uuid(store_param)
        org_node_id = read_uuid(org_param)
        user_id = read_uuid(user_param)
        if store_id is None and org_node_id is None and user_id is None:
            return None
        if not scope.allows(
            store_id=store_id, org_node_id=org_node_id, user_id=user_id
        ):
            raise_api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code="DATA_SCOPE_DENIED",
                message="当前用户数据范围不足",
            )
        if user_id and user_id != current_user.id and not scope.allows(user_id=user_id):
            raise_api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code="DATA_SCOPE_DENIED",
                message="当前用户数据范围不足",
            )
        return None

    return dependency
