from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.medication_plan import MedicationPlan
from app.models.medicine import Medicine
from app.models.reminder_time import ReminderTime
from app.schemas.plan import PlanCreate, PlanDetail, PlanUpdate, validate_date_range, validate_schedule


class PlanNotFoundError(Exception):
    pass


class MedicineNotFoundError(Exception):
    pass


def _plan_options():
    return (
        selectinload(MedicationPlan.medicine),
        selectinload(MedicationPlan.reminder_times),
    )


def _get_owned_medicine(db: Session, medicine_id: int, user_id: int) -> Medicine:
    medicine = db.scalar(
        select(Medicine).where(
            Medicine.id == medicine_id,
            Medicine.user_id == user_id,
        )
    )
    if medicine is None:
        raise MedicineNotFoundError
    return medicine


def _get_owned_plan(db: Session, plan_id: int, user_id: int) -> MedicationPlan:
    plan = db.scalar(
        select(MedicationPlan)
        .where(
            MedicationPlan.id == plan_id,
            MedicationPlan.user_id == user_id,
            MedicationPlan.deleted_at.is_(None),
        )
        .options(*_plan_options())
    )
    if plan is None:
        raise PlanNotFoundError
    return plan


def _to_detail(plan: MedicationPlan) -> PlanDetail:
    return PlanDetail(
        id=plan.id,
        user_id=plan.user_id,
        medicine_id=plan.medicine_id,
        medicine={
            "id": plan.medicine.id,
            "name": plan.medicine.name,
            "specification": getattr(plan.medicine, "specification", None),
        },
        dose=plan.dose,
        daily_times=plan.daily_times,
        start_date=plan.start_date,
        end_date=plan.end_date,
        remark=plan.remark,
        is_enabled=plan.is_enabled,
        reminder_times=[
            item.reminder_time.strftime("%H:%M")
            for item in sorted(
                plan.reminder_times,
                key=lambda item: item.reminder_time,
            )
        ],
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def list_plans(db: Session, user_id: int) -> list[PlanDetail]:
    plans = db.scalars(
        select(MedicationPlan)
        .where(
            MedicationPlan.user_id == user_id,
            MedicationPlan.deleted_at.is_(None),
        )
        .options(*_plan_options())
        .order_by(MedicationPlan.created_at.desc(), MedicationPlan.id.desc())
    ).all()
    return [_to_detail(plan) for plan in plans]


def get_plan(db: Session, plan_id: int, user_id: int) -> PlanDetail:
    return _to_detail(_get_owned_plan(db, plan_id, user_id))


def create_plan(db: Session, payload: PlanCreate, user_id: int) -> PlanDetail:
    _get_owned_medicine(db, payload.medicine_id, user_id)
    plan = MedicationPlan(
        user_id=user_id,
        medicine_id=payload.medicine_id,
        dose=payload.dose,
        daily_times=payload.daily_times,
        start_date=payload.start_date,
        end_date=payload.end_date,
        remark=payload.remark,
        is_enabled=payload.is_enabled,
        reminder_times=[
            ReminderTime(reminder_time=reminder_time)
            for reminder_time in payload.reminder_times
        ],
    )
    try:
        db.add(plan)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return get_plan(db, plan.id, user_id)


def update_plan(
    db: Session,
    plan_id: int,
    payload: PlanUpdate,
    user_id: int,
) -> PlanDetail:
    plan = _get_owned_plan(db, plan_id, user_id)
    fields = payload.model_fields_set

    daily_times = (
        payload.daily_times if "daily_times" in fields else plan.daily_times
    )
    reminder_times = (
        payload.reminder_times
        if "reminder_times" in fields
        else [item.reminder_time for item in plan.reminder_times]
    )
    start_date = payload.start_date if "start_date" in fields else plan.start_date
    end_date = payload.end_date if "end_date" in fields else plan.end_date

    validate_schedule(daily_times, reminder_times)
    validate_date_range(start_date, end_date)

    if "dose" in fields:
        plan.dose = payload.dose
    if "daily_times" in fields:
        plan.daily_times = payload.daily_times
    if "start_date" in fields:
        plan.start_date = payload.start_date
    if "end_date" in fields:
        plan.end_date = payload.end_date
    if "remark" in fields:
        plan.remark = payload.remark
    if "is_enabled" in fields:
        plan.is_enabled = payload.is_enabled
    if "reminder_times" in fields:
        plan.reminder_times = [
            ReminderTime(reminder_time=reminder_time)
            for reminder_time in payload.reminder_times
        ]

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return get_plan(db, plan_id, user_id)


def delete_plan(db: Session, plan_id: int, user_id: int) -> None:
    plan = _get_owned_plan(db, plan_id, user_id)
    plan.is_enabled = False
    plan.deleted_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
