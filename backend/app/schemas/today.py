from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


MedicationStatus = Literal["pending", "taken", "skipped", "snoozed"]
LogAction = Literal["taken", "skipped", "snoozed"]
GroupStatus = Literal["pending", "done", "snoozed"]


class MedicationLogCreate(BaseModel):
    reminder_group_id: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}_(?:[01]\d|2[0-3]):[0-5]\d$")
    status: LogAction

    model_config = ConfigDict(extra="forbid")


class TodayMedicine(BaseModel):
    medicine_id: int
    plan_id: int
    name: str
    dosage: str
    status: MedicationStatus
    planned_at: datetime
    actual_at: datetime | None = None
    snooze_until: datetime | None = None


class TodayItem(BaseModel):
    reminder_group_id: str
    time: str
    period: str
    plan_ids: list[int]
    speech_text: str
    status: GroupStatus
    medicines: list[TodayMedicine]


class TodaySummary(BaseModel):
    total: int
    done: int
    pending: int


class TodayResponse(BaseModel):
    date: date
    timezone: str
    nickname: str
    greeting: str
    summary: TodaySummary
    items: list[TodayItem]
