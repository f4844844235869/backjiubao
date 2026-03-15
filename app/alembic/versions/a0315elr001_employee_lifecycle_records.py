"""新增员工任职记录表

Revision ID: a0315elr001
Revises: a0315ueml001
Create Date: 2026-03-15 14:30:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "a0315elr001"
down_revision = "a0315ueml001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "employee_employment_record",
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
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("org_node_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("position_name", sa.String(length=100), nullable=True),
        sa.Column("leave_reason", sa.String(length=255), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_employee_employment_record_user_id",
        "employee_employment_record",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_employee_employment_record_store_id",
        "employee_employment_record",
        ["store_id"],
        unique=False,
    )
    op.create_index(
        "ix_employee_employment_record_org_node_id",
        "employee_employment_record",
        ["org_node_id"],
        unique=False,
    )

    op.execute(
        """
        INSERT INTO employee_employment_record (
            user_id,
            employee_no,
            employment_status,
            hired_at,
            left_at,
            store_id,
            org_node_id,
            position_name,
            leave_reason,
            id,
            created_at,
            updated_at
        )
        SELECT
            ep.user_id,
            ep.employee_no,
            ep.employment_status,
            ep.hired_at,
            ep.left_at,
            u.primary_store_id,
            u.primary_department_id,
            NULL,
            NULL,
            uuid_generate_v4(),
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        FROM employee_profile ep
        JOIN "user" u ON u.id = ep.user_id
        """
    )


def downgrade():
    op.drop_index(
        "ix_employee_employment_record_org_node_id",
        table_name="employee_employment_record",
    )
    op.drop_index(
        "ix_employee_employment_record_store_id",
        table_name="employee_employment_record",
    )
    op.drop_index(
        "ix_employee_employment_record_user_id",
        table_name="employee_employment_record",
    )
    op.drop_table("employee_employment_record")
