"""add role creator

Revision ID: a0315rcr001
Revises: a0315rlg001
Create Date: 2026-03-15 20:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a0315rcr001"
down_revision = "a0315rlg001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "role",
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_role_created_by_user_id_user",
        "role",
        "user",
        ["created_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_role_created_by_user_id"),
        "role",
        ["created_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_role_created_by_user_id"), table_name="role")
    op.drop_constraint("fk_role_created_by_user_id_user", "role", type_="foreignkey")
    op.drop_column("role", "created_by_user_id")
