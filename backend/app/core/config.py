from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Take Medicine API"
    app_env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "mysql+pymysql://take_user:take_pass123@127.0.0.1:3306/take_medicine?charset=utf8mb4"

    redis_url: str = "redis://127.0.0.1:6379/0"

    jwt_secret_key: str = "please-change-this-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080

    sms_mode: str = "mock"
    sms_test_code: str = "123456"
    sms_code_expire_seconds: int = 300
    sms_send_cooldown_seconds: int = 60
    sms_max_daily_send: int = 10
    sms_max_verify_attempts: int = 5
    aliyun_sms_access_key_id: str = ""
    aliyun_sms_access_key_secret: str = ""
    aliyun_sms_sign_name: str = ""
    aliyun_sms_template_code: str = ""

    ai_recognition_mode: str = "bailian"
    bailian_api_key: str = ""
    bailian_model: str = "qwen-vl-plus"
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10

    cors_origins: list[str] = Field(default_factory=lambda: ["*"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
