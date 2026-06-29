from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.medication_log import MedicationLog
from app.models.medication_plan import MedicationPlan
from app.models.medicine import Medicine
from app.models.user import User
from app.schemas.medication_log import (
    MedicationLogHistoryItem,
    MedicationLogHistoryResponse,
)


def get_history(
    db: Session,
    user: User,
    *,
    limit: int,
    offset: int,
) -> MedicationLogHistoryResponse:
    user_filter = MedicationPlan.user_id == user.id
    try:
        user_timezone = ZoneInfo(user.timezone or "Asia/Shanghai")
    except (ZoneInfoNotFoundError, ValueError):
        user_timezone = ZoneInfo("Asia/Shanghai")

    def local_time(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        source = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        return source.astimezone(user_timezone)

    total = db.scalar(
        select(func.count())
        .select_from(MedicationLog)
        .join(MedicationPlan, MedicationPlan.id == MedicationLog.plan_id)
        .where(user_filter)
    ) or 0

    rows = db.execute(
        select(MedicationLog, MedicationPlan, Medicine)
        .join(MedicationPlan, MedicationPlan.id == MedicationLog.plan_id)
        .join(Medicine, Medicine.id == MedicationPlan.medicine_id)
        .where(user_filter)
        .order_by(MedicationLog.planned_at.desc(), MedicationLog.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    return MedicationLogHistoryResponse(
        items=[
            MedicationLogHistoryItem(
                id=log.id,
                plan_id=plan.id,
                medicine_id=medicine.id,
                medicine_name=medicine.name,
                dose=plan.dose,
                planned_at=local_time(log.planned_at),
                actual_at=local_time(log.actual_at),
                status=log.status,
                snooze_until=local_time(log.snooze_until),
                remark=log.remark,
            )
            for log, plan, medicine in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
