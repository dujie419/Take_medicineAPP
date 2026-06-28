from __future__ import annotations

import re
from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, field_validator, model_validator

TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def validate_schedule(daily_times: int, reminder_times: list[time]) -> None:
    if daily_times != len(reminder_times):
        raise ValueError("每日次数必须与提醒时间数量一致")
    if len(set(reminder_times)) != len(reminder_times):
        raise ValueError("同一计划内的提醒时间不能重复")


def validate_date_range(start_date: date, end_date: date | None) -> None:
    if end_date is not None and end_date < start_date:
        raise ValueError("结束日期不能早于开始日期")


def _validate_time_input(value: Any) -> Any:
    if isinstance(value, time):
        if value.second or value.microsecond:
            raise ValueError("提醒时间格式必须为 HH:mm")
        return value
    if not isinstance(value, str) or TIME_PATTERN.fullmatch(value) is None:
        raise ValueError("提醒时间格式必须为 HH:mm")
    return value


class PlanCreate(BaseModel):
    medicine_id: PositiveInt
    dose: str = Field(min_length=1, max_length=100)
    daily_times: int = Field(ge=1, le=24)
    start_date: date
    end_date: date | None = None
    remark: str | None = Field(default=None, max_length=500)
    is_enabled: bool = True
    reminder_times: list[time] = Field(min_length=1, max_length=24)

    @field_validator("dose")
    @classmethod
    def normalize_dose(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("每次剂量不能为空")
        return value

    @field_validator("remark")
    @classmethod
    def normalize_remark(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("reminder_times", mode="before")
    @classmethod
    def validate_time_format(cls, value: Any) -> Any:
        if not isinstance(value, list):
            raise ValueError("提醒时间必须为数组")
        return [_validate_time_input(item) for item in value]

    @field_validator("reminder_times")
    @classmethod
    def sort_times(cls, value: list[time]) -> list[time]:
        return sorted(value)

    @model_validator(mode="after")
    def validate_plan(self) -> PlanCreate:
        validate_schedule(self.daily_times, self.reminder_times)
        validate_date_range(self.start_date, self.end_date)
        return self


class PlanUpdate(BaseModel):
    dose: str | None = Field(default=None, min_length=1, max_length=100)
    daily_times: int | None = Field(default=None, ge=1, le=24)
    start_date: date | None = None
    end_date: date | None = None
    remark: str | None = Field(default=None, max_length=500)
    is_enabled: bool | None = None
    reminder_times: list[time] | None = Field(default=None, min_length=1, max_length=24)

    @field_validator("dose")
    @classmethod
    def normalize_dose(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("每次剂量不能为空")
        return value

    @field_validator("remark")
    @classmethod
    def normalize_remark(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("reminder_times", mode="before")
    @classmethod
    def validate_time_format(cls, value: Any) -> Any:
        if value is None:
            return None
        if not isinstance(value, list):
            raise ValueError("提醒时间必须为数组")
        return [_validate_time_input(item) for item in value]

    @field_validator("reminder_times")
    @classmethod
    def sort_times(cls, value: list[time] | None) -> list[time] | None:
        return sorted(value) if value is not None else None

    @model_validator(mode="after")
    def validate_update(self) -> PlanUpdate:
        if not self.model_fields_set:
            raise ValueError("至少需要提供一个要修改的字段")
        non_nullable_fields = {
            "dose",
            "daily_times",
            "start_date",
            "is_enabled",
            "reminder_times",
        }
        for field_name in self.model_fields_set & non_nullable_fields:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} 不能为 null")
        if self.daily_times is not None and self.reminder_times is not None:
            validate_schedule(self.daily_times, self.reminder_times)
        if self.start_date is not None and "end_date" in self.model_fields_set:
            validate_date_range(self.start_date, self.end_date)
        return self


class MedicineSummary(BaseModel):
    id: int
    name: str
    specification: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PlanDetail(BaseModel):
    id: int
    user_id: int
    medicine_id: int
    medicine: MedicineSummary
    dose: str
    daily_times: int
    start_date: date
    end_date: date | None
    remark: str | None
    is_enabled: bool
    reminder_times: list[str]
    created_at: datetime
    updated_at: datetime


class PlanList(BaseModel):
    items: list[PlanDetail]
    total: int
