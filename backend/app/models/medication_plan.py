from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.medicine import Medicine
    from app.models.reminder_time import ReminderTime
    from app.models.user import User


class MedicationPlan(Base):
    """A user's daily medication schedule.

    The table is intentionally not accompanied by an Alembic revision yet.
    That revision must be generated only after A's shared database baseline
    has been merged.
    """

    __tablename__ = "medication_plans"
    __table_args__ = (
        Index("ix_medication_plans_user_enabled", "user_id", "is_enabled"),
        Index("ix_medication_plans_active_dates", "start_date", "end_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    medicine_id: Mapped[int] = mapped_column(
        ForeignKey("medicines.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    dose: Mapped[str] = mapped_column(String(100), nullable=False)
    daily_times: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
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

    user: Mapped[User] = relationship("User")
    medicine: Mapped[Medicine] = relationship("Medicine")
    reminder_times: Mapped[list[ReminderTime]] = relationship(
        "ReminderTime",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="ReminderTime.reminder_time",
    )
