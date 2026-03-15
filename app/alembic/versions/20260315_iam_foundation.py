"""新增认证与权限基础表

Revision ID: 20260315_iam_foundation
Revises: fe56fa70289e
Create Date: 2026-03-15 04:55:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260315_iam_foundation"
down_revision = "fe56fa70289e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("username", sa.String(length=255), nullable=True))
    op.add_column("user", sa.Column("nickname", sa.String(length=255), nullable=True))
    op.add_column("user", sa.Column("mobile", sa.String(length=32), nullable=True))
    op.add_column(
        "user",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="ACTIVE",
        ),
    )
    op.add_column(
        "user",
        sa.Column("primary_store_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "user",
        sa.Column(
            "primary_department_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
    )
    op.execute('UPDATE "user" SET username = email WHERE username IS NULL')
    op.alter_column("user", "username", nullable=False)
    op.create_index("ix_user_username", "user", ["username"], unique=True)

    op.create_table(
        "role",
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_role_code", "role", ["code"], unique=True)

    op.create_table(
        "permission",
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("module", sa.String(length=100), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_permission_code", "permission", ["code"], unique=True)

    op.create_table(
        "user_role",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["role.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role_user_id_role_id"),
    )

    op.create_table(
        "role_permission",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permission.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["role.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permission_role_id_permission_id",
        ),
    )

    op.create_table(
        "user_data_scope",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scope_type", sa.String(length=20), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("org_node_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("user_data_scope")
    op.drop_table("role_permission")
    op.drop_table("user_role")
    op.drop_index("ix_permission_code", table_name="permission")
    op.drop_table("permission")
    op.drop_index("ix_role_code", table_name="role")
    op.drop_table("role")

    op.drop_index("ix_user_username", table_name="user")
    op.drop_column("user", "primary_department_id")
    op.drop_column("user", "primary_store_id")
    op.drop_column("user", "status")
    op.drop_column("user", "mobile")
    op.drop_column("user", "nickname")
    op.drop_column("user", "username")
