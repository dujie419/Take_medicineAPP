"""create ai recognition records table

Revision ID: 20260628_0004
Revises: 20260628_0003
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "20260628_0004"
down_revision: str | None = "20260628_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_recognition_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("image_path", sa.String(length=255), nullable=False),
        sa.Column("recognition_mode", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.Column("structured_result", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_recognition_records_id"), "ai_recognition_records", ["id"], unique=False)
    op.create_index(op.f("ix_ai_recognition_records_user_id"), "ai_recognition_records", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_recognition_records_user_id"), table_name="ai_recognition_records")
    op.drop_index(op.f("ix_ai_recognition_records_id"), table_name="ai_recognition_records")
    op.drop_table("ai_recognition_records")
