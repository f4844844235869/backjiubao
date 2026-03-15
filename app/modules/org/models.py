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
    from app.modules.store.models import Store


class OrgNodeBase(SQLModel):
    store_id: uuid.UUID = Field(foreign_key="store.id", description="门店 ID")
    parent_id: uuid.UUID | None = Field(default=None, description="父节点 ID")
    name: str = Field(max_length=100, description="组织名称")
    prefix: str = Field(default="ORG", max_length=20, description="组织编号前缀")
    node_type: str = Field(max_length=30, description="组织节点类型")
    path: str = Field(max_length=500, description="物化路径")
    level: int = Field(ge=1, description="层级")
    sort_order: int = Field(default=0, description="排序值")
    is_active: bool = Field(default=True, description="是否启用")


class OrgNodeCreate(SQLModel):
    store_id: uuid.UUID = Field(description="门店 ID")
    parent_id: uuid.UUID | None = Field(default=None, description="父节点 ID")
    name: str = Field(max_length=100, description="组织名称")
    prefix: str = Field(default="ORG", max_length=20, description="组织编号前缀")
    node_type: str = Field(max_length=30, description="组织节点类型")
    sort_order: int = Field(default=0, description="排序值")
    is_active: bool = Field(default=True, description="是否启用")


class OrgNodeUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=100, description="组织名称")
    prefix: str | None = Field(default=None, max_length=20, description="组织编号前缀")
    sort_order: int | None = Field(default=None, description="排序值")
    is_active: bool | None = Field(default=None, description="是否启用")


class OrgNode(OrgNodeBase, table=True):
    __tablename__ = "org_node"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="创建时间",
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="更新时间",
    )
    store: "Store" = Relationship(back_populates="org_nodes")
    user_bindings: list["UserOrgBinding"] = Relationship(back_populates="org_node")


class OrgNodePublic(OrgNodeBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class UserOrgBindingBase(SQLModel):
    user_id: uuid.UUID = Field(foreign_key="user.id", description="用户 ID")
    org_node_id: uuid.UUID = Field(
        foreign_key="org_node.id", description="组织节点 ID"
    )
    is_primary: bool = Field(default=False, description="是否主归属")
    position_name: str | None = Field(
        default=None, max_length=100, description="岗位名称"
    )


class UserOrgBindingCreate(UserOrgBindingBase):
    pass


class UserOrgBindingUpdate(SQLModel):
    org_node_id: uuid.UUID | None = Field(default=None, description="目标组织节点 ID")
    is_primary: bool | None = Field(default=None, description="是否主归属")
    position_name: str | None = Field(
        default=None, max_length=100, description="岗位名称"
    )


class UserOrgBinding(UserOrgBindingBase, table=True):
    __tablename__ = "user_org_binding"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="创建时间",
    )

    user: "User" = Relationship(back_populates="org_bindings")
    org_node: "OrgNode" = Relationship(back_populates="user_bindings")


class UserOrgBindingPublic(UserOrgBindingBase):
    id: uuid.UUID
    created_at: datetime


class OrgNodeMemberPublic(SQLModel):
    user: UserPublic = Field(description="用户基础信息")
    employee_no: str | None = Field(default=None, description="员工编号")
    employment_status: str | None = Field(default=None, description="员工任职状态")
    store_id: uuid.UUID = Field(description="门店 ID")
    store_name: str = Field(description="门店名称")
    org_node_id: uuid.UUID = Field(description="组织节点 ID")
    org_node_name: str = Field(description="组织节点名称")
    position_name: str | None = Field(default=None, description="岗位名称")
    is_primary: bool = Field(description="是否主归属")


class OrgNodeMembersResponse(SQLModel):
    org_nodes: list[OrgNodePublic] = Field(description="涉及到的组织节点列表")
    members: list[OrgNodeMemberPublic] = Field(description="平铺的组织成员列表")
