from datetime import datetime, timedelta
import json
import secrets

from fastapi import HTTPException, status
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings
from app.core.security import hash_sms_code, verify_sms_code


class SmsService:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.settings = get_settings()

    def send_code(self, phone: str) -> None:
        mode = self.settings.sms_mode.lower()
        if mode not in {"mock", "aliyun"}:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="短信服务模式配置错误，请联系管理员",
            )

        daily_key = self._daily_key(phone)
        cooldown_key = self._cooldown_key(phone)
        try:
            if self.redis.exists(cooldown_key):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="验证码发送过于频繁，请稍后再试",
                )

            daily_count = int(self.redis.get(daily_key) or 0)
            if daily_count >= self.settings.sms_max_daily_send:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="今日验证码发送次数已达上限",
                )

            code = self._generate_code()
            code_hash = hash_sms_code(phone, code)

            self.redis.setex(self._code_key(phone), self.settings.sms_code_expire_seconds, code_hash)
            self.redis.delete(self._attempts_key(phone))
            self.redis.setex(cooldown_key, self.settings.sms_send_cooldown_seconds, "1")

            if self.redis.incr(daily_key) == 1:
                self.redis.expireat(daily_key, self._end_of_day_timestamp())
        except RedisError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis 服务不可用，请确认验证码缓存服务已启动",
            ) from exc

        if mode == "aliyun":
            try:
                self._send_by_provider(phone, code)
            except HTTPException:
                self._cleanup_failed_send(phone, daily_key)
                raise
            except Exception as exc:
                self._cleanup_failed_send(phone, daily_key)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="短信发送失败，请稍后重试",
                ) from exc

    def verify_code(self, phone: str, code: str) -> None:
        try:
            code_key = self._code_key(phone)
            stored_hash = self.redis.get(code_key)
            if not stored_hash:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误或已过期")

            attempts_key = self._attempts_key(phone)
            attempts = int(self.redis.get(attempts_key) or 0)
            if attempts >= self.settings.sms_max_verify_attempts:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误次数过多，请重新获取")

            if not verify_sms_code(phone, code, stored_hash):
                attempts = self.redis.incr(attempts_key)
                self.redis.expire(attempts_key, self.settings.sms_code_expire_seconds)
                remaining = max(self.settings.sms_max_verify_attempts - attempts, 0)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"验证码错误，还可尝试 {remaining} 次")

            self.redis.delete(code_key, attempts_key, self._cooldown_key(phone))
        except RedisError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis 服务不可用，请确认验证码缓存服务已启动",
            ) from exc

    def _generate_code(self) -> str:
        if self.settings.sms_mode.lower() == "mock":
            return self.settings.sms_test_code
        return f"{secrets.randbelow(1000000):06d}"

    def _send_by_provider(self, phone: str, code: str) -> None:
        if self.settings.sms_mode.lower() == "aliyun":
            self._send_by_aliyun(phone, code)
            return

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="短信服务模式配置错误，请联系管理员",
        )

    def _send_by_aliyun(self, phone: str, code: str) -> None:
        missing_config = [
            value
            for value in (
                self.settings.aliyun_sms_access_key_id,
                self.settings.aliyun_sms_access_key_secret,
                self.settings.aliyun_sms_sign_name,
                self.settings.aliyun_sms_template_code,
            )
            if not value
        ]
        if missing_config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="短信服务配置不完整，请联系管理员",
            )

        try:
            client = self._create_aliyun_client()
            request = self._create_aliyun_request(phone, code)
            response = client.send_sms_with_options(request, self._create_aliyun_runtime_options())
            response_code = getattr(getattr(response, "body", None), "code", None)
            if response_code != "OK":
                raise RuntimeError(response_code or "UNKNOWN")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="短信发送失败，请稍后重试",
            ) from exc

    def _create_aliyun_client(self):
        try:
            from alibabacloud_dysmsapi20170525.client import Client as DysmsapiClient
            from alibabacloud_tea_openapi import models as open_api_models
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="短信服务依赖未安装，请联系管理员",
            ) from exc

        config = open_api_models.Config(
            access_key_id=self.settings.aliyun_sms_access_key_id,
            access_key_secret=self.settings.aliyun_sms_access_key_secret,
        )
        config.endpoint = "dysmsapi.aliyuncs.com"
        return DysmsapiClient(config)

    def _create_aliyun_request(self, phone: str, code: str):
        try:
            from alibabacloud_dysmsapi20170525 import models as dysmsapi_models
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="短信服务依赖未安装，请联系管理员",
            ) from exc

        return dysmsapi_models.SendSmsRequest(
            phone_numbers=phone,
            sign_name=self.settings.aliyun_sms_sign_name,
            template_code=self.settings.aliyun_sms_template_code,
            template_param=json.dumps({"code": code}, ensure_ascii=False),
        )

    def _create_aliyun_runtime_options(self):
        try:
            from alibabacloud_tea_util import models as util_models
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="短信服务依赖未安装，请联系管理员",
            ) from exc

        return util_models.RuntimeOptions()

    def _cleanup_failed_send(self, phone: str, daily_key: str) -> None:
        try:
            self.redis.delete(self._code_key(phone), self._attempts_key(phone), self._cooldown_key(phone))
            if int(self.redis.get(daily_key) or 0) > 0:
                self.redis.decr(daily_key)
        except RedisError:
            pass

    @staticmethod
    def _code_key(phone: str) -> str:
        return f"sms:code:{phone}"

    @staticmethod
    def _attempts_key(phone: str) -> str:
        return f"sms:attempts:{phone}"

    @staticmethod
    def _cooldown_key(phone: str) -> str:
        return f"sms:cooldown:{phone}"

    @staticmethod
    def _daily_key(phone: str) -> str:
        today = datetime.now().strftime("%Y%m%d")
        return f"sms:daily:{phone}:{today}"

    @staticmethod
    def _end_of_day_timestamp() -> int:
        now = datetime.now()
        tomorrow = now.date() + timedelta(days=1)
        end_of_day = datetime.combine(tomorrow, datetime.min.time())
        return int(end_of_day.timestamp())
