from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


MedicationLogStatus = Literal["taken", "skipped", "snoozed"]


class MedicationLogHistoryItem(BaseModel):
    id: int
    plan_id: int
    medicine_id: int
    medicine_name: str
    dose: str
    planned_at: datetime
    actual_at: datetime | None = None
    status: MedicationLogStatus
    snooze_until: datetime | None = None
    remark: str | None = None


class MedicationLogHistoryResponse(BaseModel):
    items: list[MedicationLogHistoryItem]
    total: int
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
