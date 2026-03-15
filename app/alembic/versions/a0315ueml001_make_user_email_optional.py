"""用户邮箱改为非必填

Revision ID: a0315ueml001
Revises: a0315uidf001
Create Date: 2026-03-15 10:50:00

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "a0315ueml001"
down_revision = "a0315uidf001"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "user",
        "email",
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade():
    op.alter_column(
        "user",
        "email",
        existing_type=sa.String(length=255),
        nullable=False,
    )
