import pytest
from pydantic import ValidationError

from app.schemas.today import MedicationLogCreate


@pytest.mark.parametrize("status", ["taken", "skipped", "snoozed"])
def test_medication_log_action_accepts_supported_statuses(status):
    payload = MedicationLogCreate(
        reminder_group_id="2026-06-29_08:00",
        status=status,
    )

    assert payload.status == status


@pytest.mark.parametrize(
    "group_id",
    ["2026-06-29_8:00", "2026-06-29_24:00", "not-a-group"],
)
def test_medication_log_action_requires_stable_group_id(group_id):
    with pytest.raises(ValidationError):
        MedicationLogCreate(reminder_group_id=group_id, status="taken")


def test_medication_log_action_rejects_unknown_status():
    with pytest.raises(ValidationError):
        MedicationLogCreate(
            reminder_group_id="2026-06-29_08:00",
            status="done",
        )


def test_medication_log_action_rejects_plan_ids_from_client():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        MedicationLogCreate(
            reminder_group_id="2026-06-29_08:00",
            status="taken",
            plan_ids=[1],
        )
