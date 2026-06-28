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


class MedicineRead(MedicineBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
