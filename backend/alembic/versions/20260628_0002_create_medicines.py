"""create medicines table

Revision ID: 20260628_0002
Revises: 20260628_0001
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "20260628_0002"
down_revision: str | None = "20260628_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "medicines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("specification", sa.String(length=100), nullable=True),
        sa.Column("dosage", sa.String(length=100), nullable=True),
        sa.Column("usage_note", sa.Text(), nullable=True),
        sa.Column("original_image_path", sa.String(length=255), nullable=True),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_medicines_id"), "medicines", ["id"], unique=False)
    op.create_index(op.f("ix_medicines_user_id"), "medicines", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_medicines_user_id"), table_name="medicines")
    op.drop_index(op.f("ix_medicines_id"), table_name="medicines")
    op.drop_table("medicines")
