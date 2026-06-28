import re

from pydantic import BaseModel, Field, field_validator

from app.schemas.user import UserRead


PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")


class PhoneRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        phone = value.strip()
        if not PHONE_PATTERN.fullmatch(phone):
            raise ValueError("手机号格式不正确")
        return phone


class LoginRequest(PhoneRequest):
    code: str = Field(min_length=6, max_length=6)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        code = value.strip()
        if not code.isdigit() or len(code) != 6:
            raise ValueError("验证码必须是 6 位数字")
        return code


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
