"""add org prefix

Revision ID: a0315onp001
Revises: a0315elr001
Create Date: 2026-03-15 16:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a0315onp001"
down_revision = "a0315elr001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "org_node",
        sa.Column("prefix", sa.String(length=20), nullable=False, server_default="ORG"),
    )
    op.execute("UPDATE org_node SET prefix = 'ORG' WHERE prefix IS NULL OR prefix = ''")
    op.alter_column("org_node", "prefix", server_default=None)


def downgrade():
    op.drop_column("org_node", "prefix")
