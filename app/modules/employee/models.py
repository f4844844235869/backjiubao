# ruff: noqa: UP037
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import get_datetime_utc
from app.models.user import UserPublic
from app.modules.iam.models import DataScopePublic, RolePublic
from app.modules.org.models import UserOrgBindingPublic

if TYPE_CHECKING:
    from app.models.user import User


class EmployeeProfileBase(SQLModel):
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        description="用户 ID",
        sa_column_kwargs={"unique": True},
    )
    employee_no: str | None = Field(
        default=None,
        max_length=64,
        description="员工编号",
        sa_column_kwargs={"unique": True},
    )
    employment_status: str = Field(
        default="ACTIVE", max_length=30, description="任职状态"
    )
    hired_at: datetime | None = Field(default=None, description="入职时间")
    left_at: datetime | None = Field(default=None, description="离职时间")


class EmployeeProfileCreate(EmployeeProfileBase):
    pass


class EmployeeProfileUpdate(SQLModel):
    employee_no: str | None = Field(
        default=None, max_length=64, description="员工编号"
    )
    employment_status: str | None = Field(
        default=None, max_length=30, description="任职状态"
    )
    hired_at: datetime | None = Field(default=None, description="入职时间")
    left_at: datetime | None = Field(default=None, description="离职时间")


class EmployeeProfile(EmployeeProfileBase, table=True):
    __tablename__ = "employee_profile"

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

    user: "User" = Relationship(back_populates="employee_profile")


class EmployeeProfilePublic(EmployeeProfileBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class EmployeeEmploymentRecordBase(SQLModel):
    user_id: uuid.UUID = Field(foreign_key="user.id", description="用户 ID")
    employee_no: str | None = Field(
        default=None, max_length=64, description="当次任职员工编号"
    )
    employment_status: str = Field(
        default="ACTIVE", max_length=30, description="任职记录状态"
    )
    hired_at: datetime | None = Field(default=None, description="本次入职时间")
    left_at: datetime | None = Field(default=None, description="本次离职时间")
    store_id: uuid.UUID | None = Field(default=None, description="任职门店 ID")
    org_node_id: uuid.UUID | None = Field(default=None, description="任职组织节点 ID")
    position_name: str | None = Field(
        default=None, max_length=100, description="任职岗位名称"
    )
    leave_reason: str | None = Field(
        default=None, max_length=255, description="离职原因"
    )


class EmployeeEmploymentRecord(EmployeeEmploymentRecordBase, table=True):
    __tablename__ = "employee_employment_record"

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


class EmployeeEmploymentRecordPublic(EmployeeEmploymentRecordBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class EmployeeLeaveRequest(SQLModel):
    left_at: datetime | None = Field(default=None, description="离职时间")
    leave_reason: str | None = Field(
        default=None, max_length=255, description="离职原因"
    )


class EmployeeOnboardingUser(SQLModel):
    username: str = Field(max_length=255, description="登录账号")
    email: str | None = Field(default=None, max_length=255, description="邮箱")
    password: str = Field(min_length=8, max_length=128, description="初始密码")
    full_name: str | None = Field(default=None, max_length=255, description="姓名")
    nickname: str | None = Field(default=None, max_length=255, description="昵称")
    mobile: str | None = Field(default=None, max_length=32, description="手机号")


class EmployeeOnboardingRequest(SQLModel):
    user: EmployeeOnboardingUser = Field(description="员工账号信息")
    hired_at: datetime | None = Field(default=None, description="入职时间")
    primary_org_node_id: uuid.UUID = Field(description="主组织节点 ID")
    position_name: str | None = Field(
        default=None, max_length=100, description="岗位名称"
    )
    role_ids: list[uuid.UUID] = Field(default_factory=list, description="初始角色 ID 列表")
    scopes: list[DataScopePublic] = Field(
        default_factory=list, description="初始数据范围列表"
    )


class EmployeeOnboardingResult(SQLModel):
    user: UserPublic = Field(description="员工账号信息")
    profile: EmployeeProfilePublic = Field(description="员工档案")
    primary_binding: UserOrgBindingPublic = Field(description="主组织绑定")
    roles: list[RolePublic] = Field(default_factory=list, description="已分配角色")
    data_scopes: list[DataScopePublic] = Field(
        default_factory=list, description="已分配数据范围"
    )
