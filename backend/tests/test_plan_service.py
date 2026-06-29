from datetime import date, time

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.medication_plan import MedicationPlan
from app.models.medicine import Medicine
from app.models.reminder_time import ReminderTime
from app.models.user import User
from app.schemas.plan import PlanUpdate
from app.services.plan_service import update_plan


def test_update_plan_keeps_unchanged_reminder_without_duplicate_insert():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        user = User(
            phone="13800000000",
            nickname="测试用户",
            timezone="Asia/Shanghai",
        )
        db.add(user)
        db.flush()

        medicine = Medicine(user_id=user.id, name="阿司匹林")
        db.add(medicine)
        db.flush()

        plan = MedicationPlan(
            user_id=user.id,
            medicine_id=medicine.id,
            dose="1片",
            daily_times=1,
            start_date=date(2026, 6, 29),
            is_enabled=True,
            reminder_times=[ReminderTime(reminder_time=time(8, 0))],
        )
        db.add(plan)
        db.commit()

        result = update_plan(
            db,
            plan.id,
            PlanUpdate(
                dose="1片",
                daily_times=1,
                start_date=date(2026, 6, 29),
                end_date=None,
                remark="已通过 PUT 更新",
                is_enabled=True,
                reminder_times=[time(8, 0)],
            ),
            user.id,
        )

        reminder_count = db.scalar(
            select(func.count())
            .select_from(ReminderTime)
            .where(ReminderTime.plan_id == plan.id)
        )
        assert reminder_count == 1
        assert result.reminder_times == ["08:00"]
        assert result.remark == "已通过 PUT 更新"
