"""create medication log table

Revision ID: 20260629_0004
Revises: 20260628_0003
Create Date: 2026-06-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "20260629_0004"
down_revision: str | None = "20260628_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "medication_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("planned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("snooze_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
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
        sa.CheckConstraint(
            "status IN ('taken', 'skipped', 'snoozed')",
            name="ck_medication_logs_status",
        ),
        sa.UniqueConstraint(
            "plan_id",
            "planned_at",
            name="uq_medication_logs_plan_planned_at",
        ),
    )
    op.create_index(
        "ix_medication_logs_plan_id",
        "medication_logs",
        ["plan_id"],
        unique=False,
    )
    op.create_index(
        "ix_medication_logs_planned_at",
        "medication_logs",
        ["planned_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("medication_logs")
