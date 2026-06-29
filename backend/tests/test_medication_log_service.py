from datetime import date, datetime, time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.medication_log import MedicationLog
from app.models.medication_plan import MedicationPlan
from app.models.medicine import Medicine
from app.models.reminder_time import ReminderTime
from app.models.user import User
from app.services.medication_log_service import get_history


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def add_log(
    db: Session,
    *,
    phone: str,
    medicine_name: str,
    planned_at: datetime,
) -> tuple[User, MedicationLog]:
    user = User(phone=phone, nickname="测试用户", timezone="Asia/Shanghai")
    db.add(user)
    db.flush()
    medicine = Medicine(user_id=user.id, name=medicine_name, dosage="默认剂量")
    db.add(medicine)
    db.flush()
    plan = MedicationPlan(
        user_id=user.id,
        medicine_id=medicine.id,
        dose="1片",
        daily_times=1,
        start_date=date(2026, 6, 1),
        reminder_times=[ReminderTime(reminder_time=time(8))],
    )
    db.add(plan)
    db.flush()
    log = MedicationLog(
        plan_id=plan.id,
        planned_at=planned_at,
        actual_at=planned_at,
        status="taken",
    )
    db.add(log)
    db.commit()
    return user, log


def test_history_is_user_scoped_and_newest_first(db):
    user, older = add_log(
        db,
        phone="13800000000",
        medicine_name="阿司匹林",
        planned_at=datetime(2026, 6, 28, 0, 0),
    )
    plan = db.get(MedicationPlan, older.plan_id)
    newer = MedicationLog(
        plan_id=plan.id,
        planned_at=datetime(2026, 6, 29, 0, 0),
        status="skipped",
    )
    db.add(newer)
    add_log(
        db,
        phone="13900000000",
        medicine_name="其他用户药品",
        planned_at=datetime(2026, 6, 30, 0, 0),
    )

    result = get_history(db, user, limit=20, offset=0)

    assert result.total == 2
    assert [item.id for item in result.items] == [newer.id, older.id]
    assert result.items[0].medicine_name == "阿司匹林"
    assert result.items[0].dose == "1片"


def test_history_applies_limit_and_offset(db):
    user, first = add_log(
        db,
        phone="13800000000",
        medicine_name="阿司匹林",
        planned_at=datetime(2026, 6, 27, 0, 0),
    )
    plan = db.get(MedicationPlan, first.plan_id)
    db.add_all(
        [
            MedicationLog(
                plan_id=plan.id,
                planned_at=datetime(2026, 6, day, 0, 0),
                status="taken",
            )
            for day in (28, 29)
        ]
    )
    db.commit()

    result = get_history(db, user, limit=1, offset=1)

    assert result.total == 3
    assert len(result.items) == 1
    assert result.items[0].planned_at.isoformat() == "2026-06-28T08:00:00+08:00"
