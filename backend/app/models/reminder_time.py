from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.medication_plan import MedicationPlan


class ReminderTime(Base):
    __tablename__ = "reminder_times"
    __table_args__ = (
        UniqueConstraint(
            "plan_id",
            "reminder_time",
            name="uq_reminder_times_plan_time",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("medication_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reminder_time: Mapped[time] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    plan: Mapped[MedicationPlan] = relationship(
        "MedicationPlan",
        back_populates="reminder_times",
    )
