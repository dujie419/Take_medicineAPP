from datetime import date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.medication_log import MedicationLog
from app.models.medication_plan import MedicationPlan
from app.models.medicine import Medicine
from app.models.reminder_time import ReminderTime
from app.models.user import User
from app.schemas.today import MedicationLogCreate
from app.services.today_service import (
    ReminderGroupNotFoundError,
    get_today,
    record_group_action,
)

NOW = datetime(2026, 6, 29, 0, 0, tzinfo=timezone.utc)


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


def add_user(db: Session, *, timezone_name: str = "Asia/Shanghai", phone: str = "13800000000"):
    user = User(phone=phone, nickname="张阿姨", timezone=timezone_name)
    db.add(user)
    db.flush()
    return user


def add_plan(
    db: Session,
    user: User,
    name: str,
    reminder_values: list[time],
    *,
    enabled: bool = True,
    start_date: date = date(2026, 6, 1),
    end_date: date | None = None,
    deleted_at: datetime | None = None,
):
    medicine = Medicine(user_id=user.id, name=name, dosage="默认剂量")
    db.add(medicine)
    db.flush()
    plan = MedicationPlan(
        user_id=user.id,
        medicine_id=medicine.id,
        dose="1片",
        daily_times=len(reminder_values),
        start_date=start_date,
        end_date=end_date,
        is_enabled=enabled,
        deleted_at=deleted_at,
        reminder_times=[
            ReminderTime(reminder_time=value)
            for value in reminder_values
        ],
    )
    db.add(plan)
    db.commit()
    return plan


def test_today_groups_same_time_and_sorts_items(db):
    user = add_user(db)
    first = add_plan(db, user, "阿司匹林", [time(20), time(8)])
    second = add_plan(db, user, "二甲双胍", [time(8)])

    result = get_today(db, user, now=NOW)

    assert result.date == date(2026, 6, 29)
    assert [item.time for item in result.items] == ["08:00", "20:00"]
    morning = result.items[0]
    assert morning.reminder_group_id == "2026-06-29_08:00"
    assert morning.plan_ids == [first.id, second.id]
    assert [item.name for item in morning.medicines] == ["阿司匹林", "二甲双胍"]
    assert morning.speech_text == "张阿姨，现在早上八点了，该吃阿司匹林、二甲双胍了。"
    assert result.summary.model_dump() == {"total": 2, "done": 0, "pending": 2}


def test_today_filters_inactive_out_of_range_deleted_and_other_users(db):
    user = add_user(db)
    other_user = add_user(db, phone="13900000000")
    active = add_plan(db, user, "有效药品", [time(8)])
    add_plan(db, user, "已暂停", [time(9)], enabled=False)
    add_plan(db, user, "未开始", [time(10)], start_date=date(2026, 6, 30))
    add_plan(db, user, "已结束", [time(11)], end_date=date(2026, 6, 28))
    add_plan(db, user, "已删除", [time(12)], deleted_at=NOW)
    add_plan(db, other_user, "其他用户", [time(13)])

    result = get_today(db, user, now=NOW)

    assert [item.plan_ids for item in result.items] == [[active.id]]


def test_invalid_timezone_falls_back_to_shanghai(db):
    user = add_user(db, timezone_name="Invalid/Timezone")
    add_plan(db, user, "阿司匹林", [time(8)])

    result = get_today(db, user, now=NOW)

    assert result.timezone == "Asia/Shanghai"
    assert result.date == date(2026, 6, 29)


@pytest.mark.parametrize("status", ["taken", "skipped", "snoozed"])
def test_group_action_is_idempotent_for_all_supported_statuses(db, status):
    user = add_user(db)
    add_plan(db, user, "阿司匹林", [time(8)])
    payload = MedicationLogCreate(
        reminder_group_id="2026-06-29_08:00",
        status=status,
    )

    first = record_group_action(db, user, payload, now=NOW)
    second = record_group_action(db, user, payload, now=NOW)

    assert db.scalar(select(func.count()).select_from(MedicationLog)) == 1
    expected_group_status = "done" if status in {"taken", "skipped"} else "snoozed"
    assert first.status == expected_group_status
    assert second.status == expected_group_status
    assert second.medicines[0].status == status


def test_taken_and_skipped_mix_counts_as_processed(db):
    user = add_user(db)
    first = add_plan(db, user, "阿司匹林", [time(8)])
    second = add_plan(db, user, "二甲双胍", [time(8)])
    planned_at = datetime(2026, 6, 29, 0, 0)
    db.add(
        MedicationLog(
            plan_id=first.id,
            planned_at=planned_at,
            actual_at=planned_at,
            status="taken",
        )
    )
    db.commit()

    partial = get_today(db, user, now=NOW)
    assert partial.items[0].status == "pending"
    assert [item.status for item in partial.items[0].medicines] == ["taken", "pending"]

    db.add(
        MedicationLog(
            plan_id=second.id,
            planned_at=planned_at,
            status="skipped",
        )
    )
    db.commit()

    completed = get_today(db, user, now=NOW)
    assert completed.items[0].status == "done"
    assert completed.summary.done == 1
    assert completed.summary.pending == 0


def test_expired_snooze_returns_to_pending(db):
    user = add_user(db)
    add_plan(db, user, "阿司匹林", [time(8)])
    payload = MedicationLogCreate(
        reminder_group_id="2026-06-29_08:00",
        status="snoozed",
    )

    snoozed = record_group_action(db, user, payload, now=NOW)
    expired = get_today(db, user, now=NOW + timedelta(minutes=6))

    assert snoozed.status == "snoozed"
    assert snoozed.medicines[0].snooze_until is not None
    assert expired.items[0].status == "pending"
    assert expired.items[0].medicines[0].status == "pending"


def test_group_action_rejects_other_date_and_other_user_group(db):
    user = add_user(db)
    other_user = add_user(db, phone="13900000000")
    add_plan(db, other_user, "其他用户药品", [time(8)])

    with pytest.raises(ReminderGroupNotFoundError):
        record_group_action(
            db,
            user,
            MedicationLogCreate(
                reminder_group_id="2026-06-28_08:00",
                status="taken",
            ),
            now=NOW,
        )

    with pytest.raises(ReminderGroupNotFoundError):
        record_group_action(
            db,
            user,
            MedicationLogCreate(
                reminder_group_id="2026-06-29_08:00",
                status="taken",
            ),
            now=NOW,
        )
