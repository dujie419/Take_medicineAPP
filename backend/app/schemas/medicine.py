from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MedicineBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    specification: str | None = Field(default=None, max_length=100)
    dosage: str | None = Field(default=None, max_length=100)
    usage_note: str | None = None
    original_image_path: str | None = Field(default=None, max_length=255)
    ai_confidence: float | None = Field(default=None, ge=0, le=1)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("药品名称不能为空")
        return name

    @field_validator("specification", "dosage", "usage_note", "original_image_path")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None


class MedicineCreate(MedicineBase):
    pass


class MedicineBatchCreate(BaseModel):
    medicines: list[MedicineCreate] = Field(min_length=1, max_length=20)


class MedicineRead(MedicineBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class RecognizedMedicine(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    specification: str | None = Field(default=None, max_length=100)
    dosage: str | None = Field(default=None, max_length=100)
    daily_times: int | None = Field(default=None, ge=1, le=12)
    suggested_times: list[str] = Field(default_factory=list, max_length=12)
    usage_note: str | None = None
    confidence: float = Field(default=0, ge=0, le=1)
    risk_notice: str = "请核对药盒或医生处方"
    need_confirm: bool = True

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("药品名称不能为空")
        return name

    @field_validator("specification", "dosage", "usage_note", "risk_notice")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None

    @field_validator("suggested_times", mode="before")
    @classmethod
    def normalize_suggested_times(cls, value: list[str] | str | None) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            return [item.strip() for item in text.replace("，", ",").split(",") if item.strip()]
        return value


class MedicineRecognitionResult(BaseModel):
    document_type: str = "未知"
    medicines: list[RecognizedMedicine] = Field(default_factory=list)
    overall_risk_notice: str = "AI识别结果仅供参考，请人工确认"


class MedicineRecognitionRead(MedicineRecognitionResult):
    record_id: int
    image_path: str
    recognition_mode: str
