"""新增商品中心、会员钱包、POS、库存四条并行线基础表

Revision ID: 20260315_parallel_lines
Revises: a0315rcr001
Create Date: 2026-03-15 17:00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260315_parallel_lines"
down_revision = "a0315rcr001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # 并行线 A：商品中心
    # -----------------------------------------------------------------------
    op.create_table(
        "product_category",
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["store_id"], ["store.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "product",
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False, server_default="个"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("selling_price", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("cost_price", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("net_profit_price", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column(
            "price_display_mode",
            sa.String(length=20),
            nullable=False,
            server_default="GROSS_PROFIT",
        ),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["store_id"], ["store.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["product_category.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_code", "product", ["code"])

    op.create_table(
        "product_sku",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku_code", sa.String(length=100), nullable=False),
        sa.Column("spec_name", sa.String(length=200), nullable=True),
        sa.Column("barcode", sa.String(length=100), nullable=True),
        sa.Column("price", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("cost_price", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("net_profit_price", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column(
            "price_display_mode",
            sa.String(length=20),
            nullable=False,
            server_default="GROSS_PROFIT",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_sku_sku_code", "product_sku", ["sku_code"])

    op.create_table(
        "product_fund_limit",
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("limit_type", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["store_id"], ["store.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "product_gift_template",
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("gift_type", sa.String(length=30), nullable=False, server_default="AMOUNT"),
        sa.Column("gift_amount", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["store_id"], ["store.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # -----------------------------------------------------------------------
    # 并行线 B：会员钱包
    # -----------------------------------------------------------------------
    op.create_table(
        "wallet_member",
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("member_no", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("mobile", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("level", sa.String(length=30), nullable=False, server_default="NORMAL"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["store_id"], ["store.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("member_no"),
    )
    op.create_index("ix_wallet_member_member_no", "wallet_member", ["member_no"])

    op.create_table(
        "wallet_principal_account",
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("balance", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("total_recharged", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("total_consumed", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("is_frozen", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["member_id"], ["wallet_member.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("member_id"),
    )

    op.create_table(
        "wallet_gift_account",
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("balance", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("total_gifted", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("total_consumed", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("is_frozen", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["member_id"], ["wallet_member.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("member_id"),
    )

    op.create_table(
        "wallet_recharge_plan",
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("recharge_amount", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("gift_amount", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("gift_template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["store_id"], ["store.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "wallet_transaction",
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_type", sa.String(length=20), nullable=False),
        sa.Column("transaction_type", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("balance_before", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("balance_after", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("remark", sa.String(length=500), nullable=True),
        sa.Column("ref_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["member_id"], ["wallet_member.id"]),
        sa.ForeignKeyConstraint(["operator_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # -----------------------------------------------------------------------
    # 并行线 C：POS
    # -----------------------------------------------------------------------
    op.create_table(
        "pos_order",
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_no", sa.String(length=64), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("total_amount", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("discount_amount", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("payable_amount", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("paid_amount", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("remark", sa.String(length=500), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["store_id"], ["store.id"]),
        sa.ForeignKeyConstraint(["operator_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_no"),
    )
    op.create_index("ix_pos_order_order_no", "pos_order", ["order_no"])

    op.create_table(
        "pos_order_item",
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sku_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_name", sa.String(length=200), nullable=False),
        sa.Column("sku_code", sa.String(length=100), nullable=True),
        sa.Column("unit_price", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("quantity", sa.Numeric(precision=18, scale=4), nullable=False, server_default="1"),
        sa.Column("subtotal", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("discount_amount", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["order_id"], ["pos_order.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pos_payment",
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payment_method", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="SUCCESS"),
        sa.Column("remark", sa.String(length=500), nullable=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["order_id"], ["pos_order.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["operator_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pos_shift_handover",
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shift_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("shift_type", sa.String(length=20), nullable=False, server_default="MORNING"),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("handover_to_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cash_amount", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("total_sales", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("order_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("remark", sa.String(length=500), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["store_id"], ["store.id"]),
        sa.ForeignKeyConstraint(["operator_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # -----------------------------------------------------------------------
    # 并行线 D：库存
    # -----------------------------------------------------------------------
    op.create_table(
        "inventory_warehouse",
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("warehouse_type", sa.String(length=30), nullable=False, server_default="MAIN"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("remark", sa.String(length=500), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["store_id"], ["store.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventory_warehouse_code", "inventory_warehouse", ["code"])

    op.create_table(
        "inventory_balance",
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("unit", sa.String(length=30), nullable=False, server_default="个"),
        sa.Column("min_quantity", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["warehouse_id"], ["inventory_warehouse.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "inventory_transaction",
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transaction_type", sa.String(length=30), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("quantity_before", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("quantity_after", sa.Numeric(precision=18, scale=4), nullable=False, server_default="0"),
        sa.Column("ref_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("remark", sa.String(length=500), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["warehouse_id"], ["inventory_warehouse.id"]),
        sa.ForeignKeyConstraint(["operator_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "inventory_transfer_order",
        sa.Column("from_warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transfer_no", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="DRAFT"),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("remark", sa.String(length=500), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["from_warehouse_id"], ["inventory_warehouse.id"]),
        sa.ForeignKeyConstraint(["to_warehouse_id"], ["inventory_warehouse.id"]),
        sa.ForeignKeyConstraint(["operator_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transfer_no"),
    )
    op.create_index(
        "ix_inventory_transfer_order_transfer_no",
        "inventory_transfer_order",
        ["transfer_no"],
    )


def downgrade() -> None:
    # Inventory
    op.drop_index("ix_inventory_transfer_order_transfer_no", "inventory_transfer_order")
    op.drop_table("inventory_transfer_order")
    op.drop_table("inventory_transaction")
    op.drop_table("inventory_balance")
    op.drop_index("ix_inventory_warehouse_code", "inventory_warehouse")
    op.drop_table("inventory_warehouse")
    # POS
    op.drop_table("pos_shift_handover")
    op.drop_table("pos_payment")
    op.drop_table("pos_order_item")
    op.drop_index("ix_pos_order_order_no", "pos_order")
    op.drop_table("pos_order")
    # Wallet
    op.drop_table("wallet_transaction")
    op.drop_table("wallet_recharge_plan")
    op.drop_table("wallet_gift_account")
    op.drop_table("wallet_principal_account")
    op.drop_index("ix_wallet_member_member_no", "wallet_member")
    op.drop_table("wallet_member")
    # Product
    op.drop_table("product_gift_template")
    op.drop_table("product_fund_limit")
    op.drop_index("ix_product_sku_sku_code", "product_sku")
    op.drop_table("product_sku")
    op.drop_index("ix_product_code", "product")
    op.drop_table("product")
    op.drop_table("product_category")
