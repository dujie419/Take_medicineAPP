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
    inspector = sa.inspect(op.get_bind())
    existing_tables = set(inspector.get_table_names())

    if "ai_recognition_records" not in existing_tables:
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

    existing_indexes = {
        index["name"]
        for index in inspector.get_indexes("ai_recognition_records")
    }
    id_index = op.f("ix_ai_recognition_records_id")
    user_id_index = op.f("ix_ai_recognition_records_user_id")

    if id_index not in existing_indexes:
        op.create_index(id_index, "ai_recognition_records", ["id"], unique=False)
    if user_id_index not in existing_indexes:
        op.create_index(user_id_index, "ai_recognition_records", ["user_id"], unique=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "ai_recognition_records" not in set(inspector.get_table_names()):
        return

    op.drop_table("ai_recognition_records")
