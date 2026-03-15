# ruff: noqa: UP037
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import get_datetime_utc

if TYPE_CHECKING:
    from app.models.user import User


class NotificationBase(SQLModel):
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        index=True,
        description="接收用户 ID",
    )
    notification_type: str = Field(max_length=50, description="通知类型")
    title: str = Field(max_length=100, description="通知标题")
    content: str = Field(max_length=500, description="通知内容")
    is_read: bool = Field(default=False, description="是否已读")


class Notification(NotificationBase, table=True):
    __tablename__ = "notification"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    read_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
        description="已读时间",
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
    user: "User" = Relationship(back_populates="notifications")


class NotificationPublic(NotificationBase):
    id: uuid.UUID
    read_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class NotificationListResponse(SQLModel):
    items: list[NotificationPublic] = Field(description="通知列表")
    unread_count: int = Field(description="未读数量")
