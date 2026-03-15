# ruff: noqa: UP037
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import get_datetime_utc

if TYPE_CHECKING:
    from app.models.item import Item
    from app.modules.employee.models import EmployeeProfile
    from app.modules.iam.models import UserDataScope, UserRole
    from app.modules.miniapp.models import MiniappAccount, UserPhoneBinding
    from app.modules.notification.models import Notification
    from app.modules.org.models import UserOrgBinding


class UserBase(SQLModel):
    user_type: str = Field(
        default="EMPLOYEE", max_length=30, description="用户类型"
    )
    username: str = Field(
        unique=True, index=True, max_length=255, description="登录账号"
    )
    email: EmailStr | None = Field(  # type: ignore
        default=None,
        unique=True,
        index=True,
        max_length=255,
        description="邮箱",
    )
    is_active: bool = Field(default=True, description="是否启用")
    is_superuser: bool = Field(default=False, description="是否为超级管理员")
    full_name: str | None = Field(default=None, max_length=255, description="姓名")
    nickname: str | None = Field(default=None, max_length=255, description="昵称")
    mobile: str | None = Field(default=None, max_length=32, description="手机号")
    status: str = Field(default="ACTIVE", max_length=20, description="账号状态")
    primary_store_id: uuid.UUID | None = Field(default=None, description="主门店 ID")
    primary_department_id: uuid.UUID | None = Field(
        default=None, description="主部门 ID"
    )


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128, description="登录密码")


class UserRegister(SQLModel):
    username: str = Field(max_length=255, description="登录账号")
    email: EmailStr | None = Field(default=None, max_length=255, description="邮箱")  # type: ignore
    password: str = Field(min_length=8, max_length=128, description="登录密码")
    full_name: str | None = Field(default=None, max_length=255, description="姓名")


class UserUpdate(UserBase):
    username: str | None = Field(default=None, max_length=255, description="登录账号")
    email: EmailStr | None = Field(default=None, max_length=255, description="邮箱")  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)
    nickname: str | None = Field(default=None, max_length=255, description="昵称")
    mobile: str | None = Field(default=None, max_length=32, description="手机号")
    status: str | None = Field(default=None, max_length=20, description="账号状态")
    primary_store_id: uuid.UUID | None = Field(default=None, description="主门店 ID")
    primary_department_id: uuid.UUID | None = Field(
        default=None, description="主部门 ID"
    )


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255, description="姓名")
    nickname: str | None = Field(default=None, max_length=255, description="昵称")
    mobile: str | None = Field(default=None, max_length=32, description="手机号")
    email: EmailStr | None = Field(default=None, max_length=255, description="邮箱")


class UpdatePassword(SQLModel):
    current_password: str = Field(
        min_length=8, max_length=128, description="当前密码"
    )
    new_password: str = Field(min_length=8, max_length=128, description="新密码")


class ResetUserPassword(SQLModel):
    new_password: str = Field(min_length=8, max_length=128, description="新密码")


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    last_login_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="最后登录时间",
    )
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="更新时间",
    )
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    employee_profile: "EmployeeProfile" = Relationship(back_populates="user")
    miniapp_accounts: list["MiniappAccount"] = Relationship(back_populates="user")
    phone_bindings: list["UserPhoneBinding"] = Relationship(back_populates="user")
    user_roles: list["UserRole"] = Relationship(back_populates="user")
    data_scopes: list["UserDataScope"] = Relationship(back_populates="user")
    org_bindings: list["UserOrgBinding"] = Relationship(back_populates="user")
    notifications: list["Notification"] = Relationship(back_populates="user")


class UserPublic(UserBase):
    id: uuid.UUID
    last_login_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int
