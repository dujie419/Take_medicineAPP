import pytest
from pydantic import ValidationError

from app.schemas.medicine import MedicineBatchCreate, MedicineRecognitionResult


def test_batch_create_requires_at_least_one_medicine() -> None:
    with pytest.raises(ValidationError):
        MedicineBatchCreate.model_validate({"medicines": []})


def test_batch_create_validates_medicine_name() -> None:
    with pytest.raises(ValidationError):
        MedicineBatchCreate.model_validate({"medicines": [{"name": "   "}]})


def test_batch_create_accepts_ai_confirmed_medicine() -> None:
    payload = MedicineBatchCreate.model_validate(
        {
            "medicines": [
                {
                    "name": "阿司匹林",
                    "specification": "100mg",
                    "dosage": "每次 1 片",
                    "usage_note": "饭后服用",
                    "original_image_path": "uploads/user_1/recognition/example.jpg",
                    "ai_confidence": 0.86,
                }
            ]
        }
    )

    assert payload.medicines[0].ai_confidence == 0.86


def test_recognition_result_accepts_string_suggested_times() -> None:
    result = MedicineRecognitionResult.model_validate(
        {
            "document_type": "处方",
            "medicines": [
                {
                    "name": "阿莫西林胶囊",
                    "specification": "0.25g",
                    "dosage": "每次0.25g，每日3次",
                    "daily_times": 3,
                    "suggested_times": "饭后服用",
                    "usage_note": "请遵医嘱服用。",
                    "confidence": 0.95,
                    "risk_notice": "请核对处方和说明书。",
                    "need_confirm": False,
                }
            ],
            "overall_risk_notice": "AI识别结果仅供参考，请人工确认",
        }
    )

    assert result.medicines[0].suggested_times == ["饭后服用"]
