"""新增商品属性驱动 SKU 表

Revision ID: 20260317_product_attribute_sku
Revises: 20260316_product_center
Create Date: 2026-03-17 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260317_product_attribute_sku"
down_revision: str | Sequence[str] | None = "20260316_product_center"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_attribute",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column(
            "display_type",
            sa.String(length=32),
            nullable=False,
            server_default="SELECT",
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_prod_attr_code"),
    )
    op.create_index(
        "idx_product_attribute_sort_order",
        "product_attribute",
        ["sort_order"],
    )

    op.create_table(
        "product_attribute_value",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("attribute_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["attribute_id"],
            ["product_attribute.id"],
            name="fk_product_attribute_value_attribute_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "attribute_id",
            "code",
            name="uq_prod_attr_val_attr_code",
        ),
        sa.UniqueConstraint(
            "attribute_id",
            "name",
            name="uq_prod_attr_val_attr_name",
        ),
    )
    op.create_index(
        "idx_product_attribute_value_attribute_id",
        "product_attribute_value",
        ["attribute_id"],
    )

    op.create_table(
        "product_attribute_assignment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("attribute_id", sa.Uuid(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["product.id"],
            name="fk_product_attribute_assignment_product_id",
        ),
        sa.ForeignKeyConstraint(
            ["attribute_id"],
            ["product_attribute.id"],
            name="fk_product_attribute_assignment_attribute_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_id",
            "attribute_id",
            name="uq_prod_attr_asg_prod_attr",
        ),
    )
    op.create_index(
        "idx_product_attribute_assignment_product_id",
        "product_attribute_assignment",
        ["product_id"],
    )

    op.create_table(
        "product_attribute_assignment_value",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("attribute_value_id", sa.Uuid(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["product_attribute_assignment.id"],
            name="fk_product_attribute_assignment_value_assignment_id",
        ),
        sa.ForeignKeyConstraint(
            ["attribute_value_id"],
            ["product_attribute_value.id"],
            name="fk_product_attribute_assignment_value_attribute_value_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "assignment_id",
            "attribute_value_id",
            name="uq_prod_attr_asg_val_asg_val",
        ),
    )
    op.create_index(
        "idx_product_attribute_assignment_value_assignment_id",
        "product_attribute_assignment_value",
        ["assignment_id"],
    )

    op.create_table(
        "product_sku_attribute_value",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sku_id", sa.Uuid(), nullable=False),
        sa.Column("attribute_id", sa.Uuid(), nullable=False),
        sa.Column("attribute_value_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["sku_id"],
            ["product_sku.id"],
            name="fk_product_sku_attribute_value_sku_id",
        ),
        sa.ForeignKeyConstraint(
            ["attribute_id"],
            ["product_attribute.id"],
            name="fk_product_sku_attribute_value_attribute_id",
        ),
        sa.ForeignKeyConstraint(
            ["attribute_value_id"],
            ["product_attribute_value.id"],
            name="fk_product_sku_attribute_value_attribute_value_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "sku_id",
            "attribute_id",
            name="uq_prod_sku_attr_val_sku_attr",
        ),
        sa.UniqueConstraint(
            "sku_id",
            "attribute_value_id",
            name="uq_prod_sku_attr_val_sku_val",
        ),
    )
    op.create_index(
        "idx_product_sku_attribute_value_sku_id",
        "product_sku_attribute_value",
        ["sku_id"],
    )
    op.create_index(
        "idx_product_sku_attribute_value_attribute_value_id",
        "product_sku_attribute_value",
        ["attribute_value_id"],
    )

    op.create_index(
        "uq_product_sku_single_default_active",
        "product_sku",
        ["product_id"],
        unique=True,
        postgresql_where=sa.text("is_default = true AND is_deleted = false"),
    )


def downgrade() -> None:
    op.drop_index("uq_product_sku_single_default_active", table_name="product_sku")
    op.drop_table("product_sku_attribute_value")
    op.drop_table("product_attribute_assignment_value")
    op.drop_table("product_attribute_assignment")
    op.drop_table("product_attribute_value")
    op.drop_table("product_attribute")
