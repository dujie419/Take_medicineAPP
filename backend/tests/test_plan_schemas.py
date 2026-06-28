from datetime import date, time

import pytest
from pydantic import ValidationError

from app.schemas.plan import PlanCreate, PlanUpdate, validate_date_range, validate_schedule


def valid_plan_data():
    return {
        "medicine_id": 1,
        "dose": "1片",
        "daily_times": 2,
        "start_date": "2026-06-28",
        "end_date": None,
        "remark": "饭后服用",
        "is_enabled": True,
        "reminder_times": ["20:00", "08:00"],
    }


def test_create_plan_normalizes_and_sorts_values():
    plan = PlanCreate.model_validate(valid_plan_data())

    assert plan.dose == "1片"
    assert plan.reminder_times == [time(8, 0), time(20, 0)]


def test_create_plan_trims_dose_and_empty_remark():
    payload = valid_plan_data()
    payload["dose"] = "  1片  "
    payload["remark"] = "   "

    plan = PlanCreate.model_validate(payload)

    assert plan.dose == "1片"
    assert plan.remark is None


def test_daily_times_must_match_reminder_count():
    payload = valid_plan_data()
    payload["daily_times"] = 3

    with pytest.raises(ValidationError, match="每日次数必须与提醒时间数量一致"):
        PlanCreate.model_validate(payload)


def test_reminder_times_must_be_unique():
    payload = valid_plan_data()
    payload["reminder_times"] = ["08:00", "08:00"]

    with pytest.raises(ValidationError, match="提醒时间不能重复"):
        PlanCreate.model_validate(payload)


@pytest.mark.parametrize("invalid_time", ["8:00", "24:00", "08:60", "08:00:30"])
def test_reminder_time_requires_hh_mm(invalid_time):
    payload = valid_plan_data()
    payload["reminder_times"] = [invalid_time, "20:00"]

    with pytest.raises(ValidationError, match="提醒时间格式必须为 HH:mm"):
        PlanCreate.model_validate(payload)


def test_end_date_cannot_precede_start_date():
    payload = valid_plan_data()
    payload["end_date"] = "2026-06-27"

    with pytest.raises(ValidationError, match="结束日期不能早于开始日期"):
        PlanCreate.model_validate(payload)


def test_same_start_and_end_date_is_allowed():
    payload = valid_plan_data()
    payload["end_date"] = payload["start_date"]

    plan = PlanCreate.model_validate(payload)

    assert plan.end_date == plan.start_date


@pytest.mark.parametrize("daily_times", [0, 25])
def test_daily_times_must_be_between_one_and_twenty_four(daily_times):
    payload = valid_plan_data()
    payload["daily_times"] = daily_times

    with pytest.raises(ValidationError):
        PlanCreate.model_validate(payload)


def test_create_rejects_unknown_fields():
    payload = valid_plan_data()
    payload["unexpected"] = "value"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        PlanCreate.model_validate(payload)


def test_update_requires_at_least_one_field():
    with pytest.raises(ValidationError, match="至少需要提供一个"):
        PlanUpdate.model_validate({})


def test_update_can_change_enabled_only():
    update = PlanUpdate.model_validate({"is_enabled": False})

    assert update.model_fields_set == {"is_enabled"}
    assert update.is_enabled is False


def test_update_allows_clearing_end_date_and_remark():
    update = PlanUpdate.model_validate({"end_date": None, "remark": None})

    assert update.model_fields_set == {"end_date", "remark"}


def test_update_rejects_attempt_to_change_medicine():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        PlanUpdate.model_validate({"medicine_id": 2})


def test_update_rejects_mismatched_complete_schedule():
    with pytest.raises(ValidationError, match="每日次数必须与提醒时间数量一致"):
        PlanUpdate.model_validate(
            {
                "daily_times": 2,
                "reminder_times": ["08:00"],
            }
        )


@pytest.mark.parametrize(
    "field_name",
    ["dose", "daily_times", "start_date", "is_enabled", "reminder_times"],
)
def test_update_rejects_null_for_required_plan_fields(field_name):
    with pytest.raises(ValidationError, match="不能为 null"):
        PlanUpdate.model_validate({field_name: None})


def test_service_validators_support_merged_update_values():
    validate_schedule(2, [time(8, 0), time(20, 0)])
    validate_date_range(date(2026, 6, 28), None)
