"""新增商品中心基础表

Revision ID: 20260316_product_center
Revises: a0315usr001
Create Date: 2026-03-16 14:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260316_product_center"
down_revision: str | Sequence[str] | None = "a0315usr001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # product_category
    op.create_table(
        "product_category",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["product_category.id"],
            name="fk_product_category_parent_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_product_category_code"),
        sa.UniqueConstraint(
            "name", "parent_id", name="uq_product_category_name_parent"
        ),
    )
    op.create_index(
        "idx_product_category_parent_id", "product_category", ["parent_id"]
    )
    op.create_index(
        "idx_product_category_is_active", "product_category", ["is_active"]
    )
    op.create_index(
        "idx_product_category_is_deleted", "product_category", ["is_deleted"]
    )

    # product
    op.create_table(
        "product",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=True),
        sa.Column("print_name", sa.String(length=64), nullable=True),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column(
            "product_type",
            sa.String(length=32),
            nullable=False,
            server_default="NORMAL",
        ),
        sa.Column("brand_name", sa.String(length=128), nullable=True),
        sa.Column("series_name", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "unit", sa.String(length=32), nullable=False, server_default="个"
        ),
        sa.Column("suggested_price", sa.Numeric(18, 2), nullable=True),
        sa.Column(
            "default_fund_usage_type",
            sa.String(length=32),
            nullable=False,
            server_default="ALL_ALLOWED",
        ),
        sa.Column(
            "is_inventory_item",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "is_commission_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "default_commission_type",
            sa.String(length=16),
            nullable=False,
            server_default="NONE",
        ),
        sa.Column(
            "default_commission_value",
            sa.Numeric(18, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "is_profit_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("standard_cost_price", sa.Numeric(18, 2), nullable=True),
        sa.Column(
            "is_storable", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "is_gift_allowed",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "is_min_consumption_eligible",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "is_front_visible",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "is_pos_visible",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "is_sale_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "is_deleted", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("remark", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["product_category.id"],
            name="fk_product_category_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_product_code"),
        sa.UniqueConstraint("name", name="uq_product_name"),
    )
    op.create_index("idx_product_category_id", "product", ["category_id"])
    op.create_index("idx_product_product_type", "product", ["product_type"])
    op.create_index("idx_product_is_active", "product", ["is_active"])
    op.create_index("idx_product_is_deleted", "product", ["is_deleted"])
    op.create_index("idx_product_is_sale_enabled", "product", ["is_sale_enabled"])

    # product_sku
    op.create_table(
        "product_sku",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("spec_text", sa.String(length=256), nullable=True),
        sa.Column("suggested_price", sa.Numeric(18, 2), nullable=True),
        sa.Column("barcode", sa.String(length=64), nullable=True),
        sa.Column(
            "is_default", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("fund_usage_type", sa.String(length=32), nullable=True),
        sa.Column("is_inventory_item", sa.Boolean(), nullable=True),
        sa.Column("is_commission_enabled", sa.Boolean(), nullable=True),
        sa.Column("commission_type", sa.String(length=16), nullable=True),
        sa.Column("commission_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("is_profit_enabled", sa.Boolean(), nullable=True),
        sa.Column("standard_cost_price", sa.Numeric(18, 2), nullable=True),
        sa.Column(
            "inventory_mode",
            sa.String(length=16),
            nullable=False,
            server_default="NONE",
        ),
        sa.Column(
            "allow_negative_inventory",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "is_sale_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "is_deleted", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["product.id"], name="fk_product_sku_product_id"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_product_sku_code"),
        sa.UniqueConstraint(
            "product_id", "name", name="uq_product_sku_product_id_name"
        ),
    )
    op.create_index("idx_product_sku_product_id", "product_sku", ["product_id"])
    op.create_index("idx_product_sku_is_default", "product_sku", ["is_default"])
    op.create_index("idx_product_sku_is_active", "product_sku", ["is_active"])
    op.create_index("idx_product_sku_is_deleted", "product_sku", ["is_deleted"])
    op.create_index(
        "idx_product_sku_is_sale_enabled", "product_sku", ["is_sale_enabled"]
    )

    # store_product
    op.create_table(
        "store_product",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column(
            "is_enabled", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "is_visible", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["product.id"], name="fk_store_product_product_id"
        ),
        sa.ForeignKeyConstraint(
            ["store_id"], ["store.id"], name="fk_store_product_store_id"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "store_id",
            "product_id",
            name="uq_store_product_store_id_product_id",
        ),
    )
    op.create_index(
        "idx_store_product_store_id", "store_product", ["store_id"]
    )
    op.create_index(
        "idx_store_product_product_id", "store_product", ["product_id"]
    )
    op.create_index(
        "idx_store_product_is_enabled", "store_product", ["is_enabled"]
    )

    # store_product_sku
    op.create_table(
        "store_product_sku",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("sku_id", sa.Uuid(), nullable=False),
        sa.Column(
            "sale_price",
            sa.Numeric(18, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column("list_price", sa.Numeric(18, 2), nullable=True),
        sa.Column("fund_usage_type", sa.String(length=32), nullable=True),
        sa.Column(
            "is_sale_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "is_visible", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "is_default", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["product.id"],
            name="fk_store_product_sku_product_id",
        ),
        sa.ForeignKeyConstraint(
            ["sku_id"],
            ["product_sku.id"],
            name="fk_store_product_sku_sku_id",
        ),
        sa.ForeignKeyConstraint(
            ["store_id"],
            ["store.id"],
            name="fk_store_product_sku_store_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "store_id", "sku_id", name="uq_store_product_sku_store_id_sku_id"
        ),
    )
    op.create_index(
        "idx_store_product_sku_store_id", "store_product_sku", ["store_id"]
    )
    op.create_index(
        "idx_store_product_sku_product_id", "store_product_sku", ["product_id"]
    )
    op.create_index(
        "idx_store_product_sku_sku_id", "store_product_sku", ["sku_id"]
    )
    op.create_index(
        "idx_store_product_sku_is_sale_enabled",
        "store_product_sku",
        ["is_sale_enabled"],
    )
    op.create_index(
        "idx_store_product_sku_effective",
        "store_product_sku",
        ["effective_from", "effective_to"],
    )

    # sku_inventory_mapping
    op.create_table(
        "sku_inventory_mapping",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sku_id", sa.Uuid(), nullable=False),
        sa.Column("inventory_product_id", sa.Uuid(), nullable=True),
        sa.Column("inventory_sku_id", sa.Uuid(), nullable=True),
        sa.Column(
            "deduct_quantity",
            sa.Numeric(18, 4),
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "deduct_unit",
            sa.String(length=32),
            nullable=False,
            server_default="个",
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["inventory_product_id"],
            ["product.id"],
            name="fk_sku_inventory_mapping_inventory_product_id",
        ),
        sa.ForeignKeyConstraint(
            ["inventory_sku_id"],
            ["product_sku.id"],
            name="fk_sku_inventory_mapping_inventory_sku_id",
        ),
        sa.ForeignKeyConstraint(
            ["sku_id"],
            ["product_sku.id"],
            name="fk_sku_inventory_mapping_sku_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_sku_inventory_mapping_sku_id", "sku_inventory_mapping", ["sku_id"]
    )
    op.create_index(
        "idx_sku_inventory_mapping_inventory_sku_id",
        "sku_inventory_mapping",
        ["inventory_sku_id"],
    )


def downgrade() -> None:
    op.drop_table("sku_inventory_mapping")
    op.drop_table("store_product_sku")
    op.drop_table("store_product")
    op.drop_table("product_sku")
    op.drop_table("product")
    op.drop_table("product_category")
