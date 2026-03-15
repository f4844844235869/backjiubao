# ruff: noqa: UP037
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import get_datetime_utc
from app.models.user import UserPublic

if TYPE_CHECKING:
    from app.models.user import User


class RoleBase(SQLModel):
    code: str = Field(index=True, unique=True, max_length=100, description="角色编码")
    name: str = Field(max_length=100, description="角色名称")
    status: str = Field(default="ACTIVE", max_length=20, description="角色状态")


class RoleUpdate(SQLModel):
    code: str | None = Field(default=None, max_length=100, description="角色编码")
    name: str | None = Field(default=None, max_length=100, description="角色名称")
    status: str | None = Field(default=None, max_length=20, description="角色状态")


class RoleManageUpdate(SQLModel):
    code: str | None = Field(default=None, max_length=100, description="角色编码")
    name: str | None = Field(default=None, max_length=100, description="角色名称")
    status: str | None = Field(default=None, max_length=20, description="角色状态")
    permission_ids: list[uuid.UUID] | None = Field(
        default=None, description="角色权限 ID 列表"
    )
    grantable_role_ids: list[uuid.UUID] | None = Field(
        default=None, description="当前角色可查看/可分配角色 ID 列表"
    )


class Role(RoleBase, table=True):
    __tablename__ = "role"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_by_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user.id",
        nullable=True,
        ondelete="SET NULL",
        description="创建用户 ID",
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    user_roles: list["UserRole"] = Relationship(back_populates="role")
    role_permissions: list["RolePermission"] = Relationship(back_populates="role")


class PermissionBase(SQLModel):
    code: str = Field(index=True, unique=True, max_length=100, description="权限编码")
    name: str = Field(max_length=100, description="权限名称")
    module: str = Field(max_length=100, description="所属模块")


class Permission(PermissionBase, table=True):
    __tablename__ = "permission"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    role_permissions: list["RolePermission"] = Relationship(
        back_populates="permission"
    )


class UserRole(SQLModel, table=True):
    __tablename__ = "user_role"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    role_id: uuid.UUID = Field(foreign_key="role.id", nullable=False, ondelete="CASCADE")
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    user: "User" = Relationship(back_populates="user_roles")
    role: Role = Relationship(back_populates="user_roles")


class RoleGrant(SQLModel, table=True):
    __tablename__ = "role_grant"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    grantor_role_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="role.id",
        nullable=True,
        ondelete="CASCADE",
        description="授权来源角色 ID",
    )
    grantor_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user.id",
        nullable=True,
        ondelete="CASCADE",
        description="授权来源用户 ID",
    )
    grantee_role_id: uuid.UUID = Field(
        foreign_key="role.id",
        nullable=False,
        ondelete="CASCADE",
        description="可查看/可分配角色 ID",
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permission"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    role_id: uuid.UUID = Field(foreign_key="role.id", nullable=False, ondelete="CASCADE")
    permission_id: uuid.UUID = Field(
        foreign_key="permission.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    role: Role = Relationship(back_populates="role_permissions")
    permission: Permission = Relationship(back_populates="role_permissions")


class UserDataScope(SQLModel, table=True):
    __tablename__ = "user_data_scope"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    scope_type: str = Field(max_length=20, description="数据范围类型")
    store_id: uuid.UUID | None = Field(default=None, description="门店 ID")
    org_node_id: uuid.UUID | None = Field(default=None, description="组织节点 ID")
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    user: "User" = Relationship(back_populates="data_scopes")


class RoleGrantRolePublic(SQLModel):
    id: uuid.UUID
    code: str
    name: str


class RolePublic(RoleBase):
    id: uuid.UUID
    created_by_user_id: uuid.UUID | None = Field(
        default=None, description="创建用户 ID"
    )
    created_at: datetime
    permission_ids: list[uuid.UUID] = Field(
        default_factory=list, description="当前角色权限 ID 列表"
    )
    permissions: list["PermissionPublic"] = Field(
        default_factory=list, description="当前角色权限列表"
    )
    grantable_role_ids: list[uuid.UUID] = Field(
        default_factory=list, description="当前角色可查看/可分配角色 ID 列表"
    )
    grantable_roles: list[RoleGrantRolePublic] = Field(
        default_factory=list, description="当前角色可查看/可分配角色列表"
    )


class PermissionPublic(PermissionBase):
    id: uuid.UUID
    created_at: datetime


class DataScopePublic(SQLModel):
    scope_type: str = Field(description="数据范围类型")
    store_id: uuid.UUID | None = Field(default=None, description="门店 ID")
    org_node_id: uuid.UUID | None = Field(default=None, description="组织节点 ID")
    scope_label: str | None = Field(default=None, description="数据范围中文说明")


class StoreMembershipPublic(SQLModel):
    store_id: uuid.UUID = Field(description="门店 ID")
    store_name: str = Field(description="门店名称")
    org_node_id: uuid.UUID | None = Field(default=None, description="组织节点 ID")
    org_node_name: str | None = Field(default=None, description="组织节点名称")
    position_name: str | None = Field(default=None, description="岗位名称")
    is_primary: bool = Field(description="是否主归属门店")
    is_current: bool = Field(description="是否当前门店")


class AccessibleStorePublic(SQLModel):
    store_id: uuid.UUID = Field(description="可访问门店 ID")
    store_name: str = Field(description="可访问门店名称")
    is_current: bool = Field(description="是否当前门店")


class CurrentUserProfile(UserPublic):
    primary_store_name: str | None = Field(default=None, description="主门店名称")
    primary_department_name: str | None = Field(default=None, description="主组织名称")
    current_store_id: uuid.UUID | None = Field(
        default=None, description="当前门店上下文 ID"
    )
    current_store_name: str | None = Field(default=None, description="当前门店名称")
    current_org_node_id: uuid.UUID | None = Field(
        default=None, description="当前组织节点上下文 ID"
    )
    current_org_node_name: str | None = Field(default=None, description="当前组织节点名称")
    roles: list[str] = Field(default_factory=list, description="当前用户角色编码列表")
    role_names: list[str] = Field(default_factory=list, description="当前用户角色名称列表")
    permissions: list[str] = Field(
        default_factory=list, description="当前用户权限编码列表"
    )
    permission_names: list[str] = Field(
        default_factory=list, description="当前用户权限名称列表"
    )
    data_scopes: list[DataScopePublic] = Field(
        default_factory=list, description="当前用户数据范围列表"
    )
    data_scope_labels: list[str] = Field(
        default_factory=list, description="当前用户数据范围中文说明列表"
    )
    store_memberships: list[StoreMembershipPublic] = Field(
        default_factory=list, description="用户所属门店列表"
    )
    accessible_stores: list[AccessibleStorePublic] = Field(
        default_factory=list, description="当前用户可切换门店列表"
    )


class UserAuthorizationSummary(UserPublic):
    roles: list[RolePublic] = Field(default_factory=list, description="角色列表")
    permissions: list[PermissionPublic] = Field(
        default_factory=list, description="生效权限列表"
    )
    data_scopes: list[DataScopePublic] = Field(
        default_factory=list, description="数据范围列表"
    )


class UserRoleAssign(SQLModel):
    role_ids: list[uuid.UUID] = Field(description="角色 ID 列表")


class RolePermissionAssign(SQLModel):
    permission_ids: list[uuid.UUID] = Field(description="权限 ID 列表")


class RoleGrantAssign(SQLModel):
    role_ids: list[uuid.UUID] = Field(description="可查看/可分配角色 ID 列表")


class UserDataScopeAssign(SQLModel):
    scopes: list[DataScopePublic] = Field(description="数据范围列表")
