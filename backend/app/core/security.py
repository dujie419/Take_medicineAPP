from datetime import UTC, datetime, timedelta
import hashlib
import hmac

from jose import JWTError, jwt

from app.core.config import get_settings


def hash_sms_code(phone: str, code: str) -> str:
    settings = get_settings()
    payload = f"{phone}:{code}".encode("utf-8")
    secret = settings.jwt_secret_key.encode("utf-8")
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()


def verify_sms_code(phone: str, code: str, code_hash: str) -> bool:
    expected = hash_sms_code(phone, code)
    return hmac.compare_digest(expected, code_hash)


def create_access_token(user_id: int) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int | None:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        return None

    subject = payload.get("sub")
    if subject is None:
        return None

    try:
        return int(subject)
    except ValueError:
        return None
