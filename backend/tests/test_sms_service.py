import sys
from types import ModuleType, SimpleNamespace

import pytest
from fastapi import HTTPException
from redis.exceptions import RedisError

from app.core.security import verify_sms_code
from app.services import sms_service
from app.services.sms_service import SmsService


def make_settings(**overrides):
    defaults = {
        "sms_mode": "mock",
        "sms_test_code": "123456",
        "sms_code_expire_seconds": 300,
        "sms_send_cooldown_seconds": 60,
        "sms_max_daily_send": 10,
        "sms_max_verify_attempts": 5,
        "aliyun_sms_access_key_id": "",
        "aliyun_sms_access_key_secret": "",
        "aliyun_sms_sign_name": "",
        "aliyun_sms_template_code": "",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.expireat_calls = []

    def exists(self, key):
        return key in self.values

    def get(self, key):
        return self.values.get(key)

    def setex(self, key, seconds, value):
        self.values[key] = value

    def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)

    def incr(self, key):
        value = int(self.values.get(key) or 0) + 1
        self.values[key] = str(value)
        return value

    def decr(self, key):
        value = int(self.values.get(key) or 0) - 1
        self.values[key] = str(value)
        return value

    def expire(self, key, seconds):
        return True

    def expireat(self, key, timestamp):
        self.expireat_calls.append((key, timestamp))
        return True


class FailingRedis(FakeRedis):
    def exists(self, key):
        raise RedisError("redis unavailable")


@pytest.fixture
def fake_redis():
    return FakeRedis()


def service_with_settings(monkeypatch, redis_client, settings):
    monkeypatch.setattr(sms_service, "get_settings", lambda: settings)
    return SmsService(redis_client)


def test_mock_mode_stores_test_code_without_calling_provider(monkeypatch, fake_redis):
    service = service_with_settings(monkeypatch, fake_redis, make_settings())
    monkeypatch.setattr(service, "_send_by_provider", lambda phone, code: pytest.fail("provider should not be called"))

    service.send_code("13800000000")

    stored_hash = fake_redis.get("sms:code:13800000000")
    assert verify_sms_code("13800000000", "123456", stored_hash)


def test_aliyun_mode_calls_provider_with_generated_code(monkeypatch, fake_redis):
    settings = make_settings(
        sms_mode="aliyun",
        aliyun_sms_access_key_id="id",
        aliyun_sms_access_key_secret="secret",
        aliyun_sms_sign_name="按时吃药",
        aliyun_sms_template_code="SMS_123",
    )
    service = service_with_settings(monkeypatch, fake_redis, settings)
    calls = []
    monkeypatch.setattr(service, "_generate_code", lambda: "654321")
    monkeypatch.setattr(service, "_send_by_provider", lambda phone, code: calls.append((phone, code)))

    service.send_code("13800000000")

    assert calls == [("13800000000", "654321")]
    assert verify_sms_code("13800000000", "654321", fake_redis.get("sms:code:13800000000"))


def test_aliyun_request_uses_code_template_param(monkeypatch, fake_redis):
    settings = make_settings(
        sms_mode="aliyun",
        aliyun_sms_sign_name="按时吃药",
        aliyun_sms_template_code="SMS_123",
    )
    service = service_with_settings(monkeypatch, fake_redis, settings)

    class FakeRequest:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    package = ModuleType("alibabacloud_dysmsapi20170525")
    models = ModuleType("alibabacloud_dysmsapi20170525.models")
    models.SendSmsRequest = FakeRequest
    package.models = models
    monkeypatch.setitem(sys.modules, "alibabacloud_dysmsapi20170525", package)
    monkeypatch.setitem(sys.modules, "alibabacloud_dysmsapi20170525.models", models)

    request = service._create_aliyun_request("13800000000", "654321")

    assert request.kwargs == {
        "phone_numbers": "13800000000",
        "sign_name": "按时吃药",
        "template_code": "SMS_123",
        "template_param": '{"code": "654321"}',
    }


def test_missing_aliyun_config_raises_clean_error(monkeypatch, fake_redis):
    service = service_with_settings(monkeypatch, fake_redis, make_settings(sms_mode="aliyun"))

    with pytest.raises(HTTPException) as exc_info:
        service._send_by_aliyun("13800000000", "123456")

    assert exc_info.value.status_code == 500
    assert "配置不完整" in exc_info.value.detail


def test_provider_failure_cleans_cached_code_and_cooldown(monkeypatch, fake_redis):
    settings = make_settings(
        sms_mode="aliyun",
        aliyun_sms_access_key_id="id",
        aliyun_sms_access_key_secret="secret",
        aliyun_sms_sign_name="按时吃药",
        aliyun_sms_template_code="SMS_123",
    )
    service = service_with_settings(monkeypatch, fake_redis, settings)
    monkeypatch.setattr(service, "_generate_code", lambda: "654321")

    def fail_provider(phone, code):
        raise HTTPException(status_code=502, detail="短信发送失败，请稍后重试")

    monkeypatch.setattr(service, "_send_by_provider", fail_provider)

    with pytest.raises(HTTPException) as exc_info:
        service.send_code("13800000000")

    assert exc_info.value.status_code == 502
    assert fake_redis.get("sms:code:13800000000") is None
    assert fake_redis.get("sms:cooldown:13800000000") is None
    assert fake_redis.get(next(key for key in fake_redis.values if key.startswith("sms:daily:"))) == "0"


def test_redis_unavailable_returns_503(monkeypatch):
    service = service_with_settings(monkeypatch, FailingRedis(), make_settings())

    with pytest.raises(HTTPException) as exc_info:
        service.send_code("13800000000")

    assert exc_info.value.status_code == 503


def test_cooldown_limit_is_preserved(monkeypatch, fake_redis):
    service = service_with_settings(monkeypatch, fake_redis, make_settings())
    fake_redis.setex("sms:cooldown:13800000000", 60, "1")

    with pytest.raises(HTTPException) as exc_info:
        service.send_code("13800000000")

    assert exc_info.value.status_code == 429
    assert "频繁" in exc_info.value.detail


def test_daily_limit_is_preserved(monkeypatch, fake_redis):
    settings = make_settings(sms_max_daily_send=1)
    service = service_with_settings(monkeypatch, fake_redis, settings)
    daily_key = service._daily_key("13800000000")
    fake_redis.values[daily_key] = "1"

    with pytest.raises(HTTPException) as exc_info:
        service.send_code("13800000000")

    assert exc_info.value.status_code == 429
    assert "上限" in exc_info.value.detail
