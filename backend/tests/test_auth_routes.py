from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.redis import get_redis
from app.main import app


class FakeRedis:
    """Minimal in-memory Redis replacement used by the authentication tests."""

    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    def exists(self, key: str) -> int:
        return int(key in self.data)

    def get(self, key: str) -> str | None:
        return self.data.get(key)

    def setex(self, key: str, seconds: int, value: str) -> bool:
        self.data[key] = str(value)
        return True

    def delete(self, *keys: str) -> int:
        deleted = 0
        for key in keys:
            if key in self.data:
                deleted += 1
                del self.data[key]
        return deleted

    def incr(self, key: str) -> int:
        value = int(self.data.get(key, "0")) + 1
        self.data[key] = str(value)
        return value

    def expire(self, key: str, seconds: int) -> bool:
        return key in self.data

    def expireat(self, key: str, timestamp: int) -> bool:
        return key in self.data


def test_sms_login_and_current_user_route() -> None:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)
    redis_client = FakeRedis()

    def override_db() -> Generator[Session, None, None]:
        with testing_session() as session:
            yield session

    def override_redis() -> Generator[FakeRedis, None, None]:
        yield redis_client

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis

    try:
        with TestClient(app) as client:
            sms_response = client.post(
                "/api/v1/auth/sms-codes",
                json={"phone": "13800138000"},
            )
            assert sms_response.status_code == 200
            assert sms_response.json()["code"] == 0

            login_response = client.post(
                "/api/v1/auth/login",
                json={"phone": "13800138000", "code": "123456"},
            )
            assert login_response.status_code == 200
            login_data = login_response.json()["data"]
            assert login_data["access_token"]
            assert login_data["user"]["phone"] == "13800138000"

            me_response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {login_data['access_token']}"},
            )
            assert me_response.status_code == 200
            assert me_response.json()["data"]["phone"] == "13800138000"
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_login_validation_error_is_json_and_not_not_found() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"phone": "bad-phone", "code": "123456"},
        )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == 422
    assert body["message"] == "请求参数不正确"
    assert body["data"][0]["loc"] == ["body", "phone"]
