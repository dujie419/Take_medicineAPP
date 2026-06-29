from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.medication_plan import MedicationPlan


class MedicationLog(Base):
    __tablename__ = "medication_logs"
    __table_args__ = (
        UniqueConstraint(
            "plan_id",
            "planned_at",
            name="uq_medication_logs_plan_planned_at",
        ),
        CheckConstraint(
            "status IN ('taken', 'skipped', 'snoozed')",
            name="ck_medication_logs_status",
        ),
        Index("ix_medication_logs_planned_at", "planned_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("medication_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    planned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    snooze_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    plan: Mapped[MedicationPlan] = relationship("MedicationPlan")
