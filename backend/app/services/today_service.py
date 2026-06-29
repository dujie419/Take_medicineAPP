from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.medication_log import MedicationLog
from app.models.medication_plan import MedicationPlan
from app.models.reminder_time import ReminderTime
from app.models.user import User
from app.schemas.today import MedicationLogCreate, TodayItem, TodayMedicine, TodayResponse, TodaySummary

DEFAULT_TIMEZONE = "Asia/Shanghai"
GROUP_ID_PATTERN = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})_(?P<hour>[01]\d|2[0-3]):(?P<minute>[0-5]\d)$"
)
FINAL_STATUSES = {"taken", "skipped"}


class ReminderGroupNotFoundError(Exception):
    pass


def resolve_timezone(name: str | None) -> tuple[str, ZoneInfo]:
    timezone_name = name or DEFAULT_TIMEZONE
    try:
        return timezone_name, ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        return DEFAULT_TIMEZONE, ZoneInfo(DEFAULT_TIMEZONE)


def _utc_now_naive(now: datetime | None = None) -> datetime:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).replace(tzinfo=None)


def _as_utc_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _local_datetime(day: date, reminder_time: time, tz: ZoneInfo) -> datetime:
    return datetime.combine(day, reminder_time, tzinfo=tz)


def _planned_at_db(day: date, reminder_time: time, tz: ZoneInfo) -> datetime:
    return _local_datetime(day, reminder_time, tz).astimezone(timezone.utc).replace(tzinfo=None)


def _active_plans_query(user_id: int, day: date):
    return (
        select(MedicationPlan)
        .where(
            MedicationPlan.user_id == user_id,
            MedicationPlan.is_enabled.is_(True),
            MedicationPlan.deleted_at.is_(None),
            MedicationPlan.start_date <= day,
            or_(MedicationPlan.end_date.is_(None), MedicationPlan.end_date >= day),
        )
        .options(
            selectinload(MedicationPlan.medicine),
            selectinload(MedicationPlan.reminder_times),
        )
        .order_by(MedicationPlan.id)
    )


def _chinese_number(value: int) -> str:
    digits = "零一二三四五六七八九"
    if value < 10:
        return digits[value]
    if value < 20:
        return "十" + (digits[value % 10] if value % 10 else "")
    return "二十" + (digits[value % 10] if value % 10 else "")


def _period(reminder_time: time) -> str:
    hour = reminder_time.hour
    if hour < 6:
        return "凌晨"
    if hour < 9:
        return "早上"
    if hour < 12:
        return "上午"
    if hour < 14:
        return "中午"
    if hour < 18:
        return "下午"
    return "晚上"


def _spoken_time(reminder_time: time) -> str:
    result = f"{_period(reminder_time)}{_chinese_number(reminder_time.hour)}点"
    if reminder_time.minute == 30:
        return result + "半"
    if reminder_time.minute:
        return result + f"{_chinese_number(reminder_time.minute)}分"
    return result


def _greeting(local_now: datetime) -> str:
    if 5 <= local_now.hour < 12:
        return "早上好"
    if 12 <= local_now.hour < 14:
        return "中午好"
    if 14 <= local_now.hour < 18:
        return "下午好"
    return "晚上好"


def _effective_log_status(log: MedicationLog | None, now_utc: datetime) -> str:
    if log is None:
        return "pending"
    if log.status in FINAL_STATUSES:
        return log.status
    snooze_until = _as_utc_aware(log.snooze_until)
    if log.status == "snoozed" and snooze_until is not None and snooze_until > now_utc:
        return "snoozed"
    return "pending"


def _group_status(statuses: list[str]) -> str:
    if statuses and all(status in FINAL_STATUSES for status in statuses):
        return "done"
    if statuses and all(status == "snoozed" for status in statuses):
        return "snoozed"
    return "pending"


def get_today(
    db: Session,
    user: User,
    *,
    now: datetime | None = None,
) -> TodayResponse:
    timezone_name, user_tz = resolve_timezone(user.timezone)
    now_utc = _as_utc_aware(now) or datetime.now(timezone.utc)
    local_now = now_utc.astimezone(user_tz)
    today = local_now.date()
    plans = list(db.scalars(_active_plans_query(user.id, today)).all())

    plan_ids = [plan.id for plan in plans]
    logs: list[MedicationLog] = []
    if plan_ids:
        start_utc = datetime.combine(today, time.min, tzinfo=user_tz).astimezone(timezone.utc).replace(tzinfo=None)
        end_utc = datetime.combine(today + timedelta(days=1), time.min, tzinfo=user_tz).astimezone(timezone.utc).replace(tzinfo=None)
        logs = list(
            db.scalars(
                select(MedicationLog).where(
                    MedicationLog.plan_id.in_(plan_ids),
                    MedicationLog.planned_at >= start_utc,
                    MedicationLog.planned_at < end_utc,
                )
            ).all()
        )
    logs_by_key = {
        (log.plan_id, _utc_now_naive(log.planned_at)): log
        for log in logs
    }

    grouped: dict[time, list[tuple[MedicationPlan, MedicationLog | None]]] = defaultdict(list)
    for plan in plans:
        for reminder in plan.reminder_times:
            planned_at = _planned_at_db(today, reminder.reminder_time, user_tz)
            grouped[reminder.reminder_time].append(
                (plan, logs_by_key.get((plan.id, planned_at)))
            )

    items: list[TodayItem] = []
    for reminder_time in sorted(grouped):
        medicines: list[TodayMedicine] = []
        for plan, log in grouped[reminder_time]:
            status = _effective_log_status(log, now_utc)
            medicines.append(
                TodayMedicine(
                    medicine_id=plan.medicine_id,
                    plan_id=plan.id,
                    name=plan.medicine.name,
                    dosage=plan.dose,
                    status=status,
                    planned_at=_local_datetime(today, reminder_time, user_tz),
                    actual_at=(
                        _as_utc_aware(log.actual_at).astimezone(user_tz)
                        if log and log.actual_at
                        else None
                    ),
                    snooze_until=(
                        _as_utc_aware(log.snooze_until).astimezone(user_tz)
                        if log and status == "snoozed"
                        else None
                    ),
                )
            )
        statuses = [medicine.status for medicine in medicines]
        medicine_names = "、".join(medicine.name for medicine in medicines)
        items.append(
            TodayItem(
                reminder_group_id=f"{today.isoformat()}_{reminder_time.strftime('%H:%M')}",
                time=reminder_time.strftime("%H:%M"),
                period=_period(reminder_time),
                plan_ids=[medicine.plan_id for medicine in medicines],
                speech_text=(
                    f"{user.nickname}，现在{_spoken_time(reminder_time)}了，"
                    f"该吃{medicine_names}了。"
                ),
                status=_group_status(statuses),
                medicines=medicines,
            )
        )

    done = sum(item.status == "done" for item in items)
    return TodayResponse(
        date=today,
        timezone=timezone_name,
        nickname=user.nickname,
        greeting=_greeting(local_now),
        summary=TodaySummary(
            total=len(items),
            done=done,
            pending=len(items) - done,
        ),
        items=items,
    )


def _parse_group_id(group_id: str) -> tuple[date, time]:
    match = GROUP_ID_PATTERN.fullmatch(group_id)
    if match is None:
        raise ReminderGroupNotFoundError
    try:
        day = date.fromisoformat(match.group("date"))
    except ValueError as exc:
        raise ReminderGroupNotFoundError from exc
    return day, time(int(match.group("hour")), int(match.group("minute")))


def record_group_action(
    db: Session,
    user: User,
    payload: MedicationLogCreate,
    *,
    now: datetime | None = None,
) -> TodayItem:
    timezone_name, user_tz = resolve_timezone(user.timezone)
    del timezone_name
    now_utc = _as_utc_aware(now) or datetime.now(timezone.utc)
    day, reminder_time = _parse_group_id(payload.reminder_group_id)
    if day != now_utc.astimezone(user_tz).date():
        raise ReminderGroupNotFoundError

    plans = list(
        db.scalars(
            _active_plans_query(user.id, day).where(
                MedicationPlan.reminder_times.any(
                    ReminderTime.reminder_time == reminder_time
                )
            )
        ).all()
    )
    if not plans:
        raise ReminderGroupNotFoundError

    planned_at = _planned_at_db(day, reminder_time, user_tz)
    plan_ids = [plan.id for plan in plans]
    existing_logs = {
        log.plan_id: log
        for log in db.scalars(
            select(MedicationLog).where(
                MedicationLog.plan_id.in_(plan_ids),
                MedicationLog.planned_at == planned_at,
            )
        ).all()
    }
    db_now = now_utc.astimezone(timezone.utc).replace(tzinfo=None)
    for plan in plans:
        log = existing_logs.get(plan.id)
        if log is None:
            log = MedicationLog(plan_id=plan.id, planned_at=planned_at, status=payload.status)
            db.add(log)
        log.status = payload.status
        if payload.status == "taken":
            log.actual_at = db_now
            log.snooze_until = None
        elif payload.status == "skipped":
            log.actual_at = None
            log.snooze_until = None
        else:
            log.actual_at = None
            log.snooze_until = db_now + timedelta(minutes=5)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    today = get_today(db, user, now=now_utc)
    for item in today.items:
        if item.reminder_group_id == payload.reminder_group_id:
            return item
    raise ReminderGroupNotFoundError
