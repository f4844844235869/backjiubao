# ruff: noqa: UP037
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.models.base import get_datetime_utc

if TYPE_CHECKING:
    from app.modules.iam.models import UserStoreRole
    from app.modules.org.models import OrgNode
    from app.modules.product.models import StoreProduct, StoreProductSku


class StoreBase(SQLModel):
    code: str = Field(index=True, unique=True, max_length=50, description="门店编码")
    name: str = Field(max_length=100, description="门店名称")
    status: str = Field(default="ACTIVE", max_length=20, description="门店状态")


class StoreCreate(StoreBase):
    pass


class StoreUpdate(SQLModel):
    code: str | None = Field(default=None, max_length=50, description="门店编码")
    name: str | None = Field(default=None, max_length=100, description="门店名称")
    status: str | None = Field(default=None, max_length=20, description="门店状态")


class Store(StoreBase, table=True):
    __tablename__ = "store"

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
    org_nodes: list["OrgNode"] = Relationship(back_populates="store")
    user_store_roles: list["UserStoreRole"] = Relationship(back_populates="store")
    store_products: list["StoreProduct"] = Relationship(back_populates="store")
    store_product_skus: list["StoreProductSku"] = Relationship(
        back_populates="store"
    )


class StorePublic(StoreBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
