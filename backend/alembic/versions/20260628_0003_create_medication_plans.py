"""create medication plan tables

Revision ID: 20260628_0003
Revises: 20260628_0002
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "20260628_0003"
down_revision: str | None = "20260628_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create plan tables while accepting an already-updated shared database."""
    inspector = sa.inspect(op.get_bind())
    existing_tables = set(inspector.get_table_names())

    if "medication_plans" not in existing_tables:
        op.create_table(
            "medication_plans",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("medicine_id", sa.Integer(), nullable=False),
            sa.Column("dose", sa.String(length=100), nullable=False),
            sa.Column("daily_times", sa.SmallInteger(), nullable=False),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("remark", sa.Text(), nullable=True),
            sa.Column(
                "is_enabled",
                sa.Boolean(),
                server_default=sa.text("1"),
                nullable=False,
            ),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["medicine_id"],
                ["medicines.id"],
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_medication_plans_active_dates",
            "medication_plans",
            ["start_date", "end_date"],
            unique=False,
        )
        op.create_index(
            "ix_medication_plans_deleted_at",
            "medication_plans",
            ["deleted_at"],
            unique=False,
        )
        op.create_index(
            "ix_medication_plans_medicine_id",
            "medication_plans",
            ["medicine_id"],
            unique=False,
        )
        op.create_index(
            "ix_medication_plans_user_enabled",
            "medication_plans",
            ["user_id", "is_enabled"],
            unique=False,
        )
        op.create_index(
            "ix_medication_plans_user_id",
            "medication_plans",
            ["user_id"],
            unique=False,
        )

    if "reminder_times" not in existing_tables:
        op.create_table(
            "reminder_times",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("plan_id", sa.Integer(), nullable=False),
            sa.Column("reminder_time", sa.Time(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["plan_id"],
                ["medication_plans.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "plan_id",
                "reminder_time",
                name="uq_reminder_times_plan_time",
            ),
        )
        op.create_index(
            "ix_reminder_times_plan_id",
            "reminder_times",
            ["plan_id"],
            unique=False,
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing_tables = set(inspector.get_table_names())

    if "reminder_times" in existing_tables:
        op.drop_table("reminder_times")
    if "medication_plans" in existing_tables:
        op.drop_table("medication_plans")
