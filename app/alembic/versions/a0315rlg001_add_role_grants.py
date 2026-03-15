"""add role grants

Revision ID: a0315rlg001
Revises: a0315ntf001
Create Date: 2026-03-15 18:40:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a0315rlg001"
down_revision = "a0315ntf001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "role_grant",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("grantor_role_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("grantor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("grantee_role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["grantor_role_id"], ["role.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["grantor_user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["grantee_role_id"], ["role.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_role_grant_grantor_role_id"),
        "role_grant",
        ["grantor_role_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_role_grant_grantor_user_id"),
        "role_grant",
        ["grantor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_role_grant_grantee_role_id"),
        "role_grant",
        ["grantee_role_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_role_grant_grantee_role_id"), table_name="role_grant")
    op.drop_index(op.f("ix_role_grant_grantor_user_id"), table_name="role_grant")
    op.drop_index(op.f("ix_role_grant_grantor_role_id"), table_name="role_grant")
    op.drop_table("role_grant")
