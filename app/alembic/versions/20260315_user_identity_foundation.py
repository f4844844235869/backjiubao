"""新增统一用户身份与员工档案骨架

Revision ID: a0315uidf001
Revises: 20260315_org_permission_skeleton
Create Date: 2026-03-15 08:30:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "a0315uidf001"
down_revision = "20260315_org_permission_skeleton"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column(
            "user_type",
            sa.String(length=30),
            nullable=False,
            server_default="EMPLOYEE",
        ),
    )

    op.create_table(
        "employee_profile",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_no", sa.String(length=64), nullable=True),
        sa.Column(
            "employment_status",
            sa.String(length=30),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("hired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_employee_profile_user_id"),
        sa.UniqueConstraint("employee_no", name="uq_employee_profile_employee_no"),
    )

    op.create_table(
        "miniapp_account",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("app_id", sa.String(length=100), nullable=False),
        sa.Column("openid", sa.String(length=128), nullable=False),
        sa.Column("unionid", sa.String(length=128), nullable=True),
        sa.Column("nickname", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("gender", sa.Integer(), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("province", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("language", sa.String(length=30), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("app_id", "openid", name="uq_miniapp_account_app_openid"),
    )

    op.create_table(
        "user_phone_binding",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("country_code", sa.String(length=10), nullable=False, server_default="+86"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "source",
            sa.String(length=30),
            nullable=False,
            server_default="WECHAT_MINIAPP",
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "country_code", "phone", name="uq_user_phone_binding_country_phone"
        ),
    )

    op.execute(
        """
        INSERT INTO employee_profile (
            id,
            user_id,
            employment_status,
            hired_at,
            created_at,
            updated_at
        )
        SELECT
            gen_random_uuid(),
            id,
            'ACTIVE',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        FROM "user"
        WHERE user_type = 'EMPLOYEE'
        """
    )


def downgrade():
    op.drop_table("user_phone_binding")
    op.drop_table("miniapp_account")
    op.drop_table("employee_profile")
    op.drop_column("user", "user_type")
