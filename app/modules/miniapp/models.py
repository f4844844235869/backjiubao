# ruff: noqa: UP037
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import get_datetime_utc

if TYPE_CHECKING:
    from app.models.user import User


class MiniappAccountBase(SQLModel):
    user_id: uuid.UUID = Field(foreign_key="user.id", description="用户 ID")
    app_id: str = Field(max_length=100, description="小程序 AppID", index=True)
    openid: str = Field(max_length=128, description="微信 OpenID", index=True)
    unionid: str | None = Field(default=None, max_length=128, description="微信 UnionID")
    nickname: str | None = Field(default=None, max_length=255, description="微信昵称")
    avatar_url: str | None = Field(default=None, max_length=500, description="头像地址")
    gender: int | None = Field(default=None, description="性别")
    country: str | None = Field(default=None, max_length=100, description="国家")
    province: str | None = Field(default=None, max_length=100, description="省份")
    city: str | None = Field(default=None, max_length=100, description="城市")
    language: str | None = Field(default=None, max_length=30, description="语言")


class MiniappAccount(MiniappAccountBase, table=True):
    __tablename__ = "miniapp_account"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    last_login_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="最后登录时间",
    )
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

    user: "User" = Relationship(back_populates="miniapp_accounts")


class UserPhoneBindingBase(SQLModel):
    user_id: uuid.UUID = Field(foreign_key="user.id", description="用户 ID")
    phone: str = Field(max_length=32, description="手机号", index=True)
    country_code: str = Field(default="+86", max_length=10, description="国家区号")
    is_verified: bool = Field(default=False, description="是否已验证")
    source: str = Field(default="WECHAT_MINIAPP", max_length=30, description="绑定来源")


class UserPhoneBinding(UserPhoneBindingBase, table=True):
    __tablename__ = "user_phone_binding"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    verified_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="验证时间",
    )
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

    user: "User" = Relationship(back_populates="phone_bindings")


class MiniappLinkedEmployeePublic(SQLModel):
    user_id: uuid.UUID = Field(description="员工用户 ID")
    username: str = Field(description="员工登录账号")
    full_name: str | None = Field(default=None, description="员工姓名")
    nickname: str | None = Field(default=None, description="员工昵称")
    mobile: str | None = Field(default=None, description="员工手机号")
    is_active: bool = Field(description="员工账号是否启用")
    status: str = Field(description="员工账号状态")
    primary_store_id: uuid.UUID | None = Field(default=None, description="主门店 ID")
    primary_department_id: uuid.UUID | None = Field(
        default=None, description="主组织节点 ID"
    )
    employee_no: str | None = Field(default=None, description="员工编号")
    employment_status: str | None = Field(default=None, description="任职状态")


class MiniappPhoneRelationPublic(SQLModel):
    current_store_id: uuid.UUID | None = Field(
        default=None, description="当前门店上下文 ID"
    )
    phone: str | None = Field(default=None, description="已绑定手机号")
    country_code: str | None = Field(default=None, description="国家区号")
    related_employees: list[MiniappLinkedEmployeePublic] = Field(
        default_factory=list, description="通过手机号关联到的员工列表"
    )
