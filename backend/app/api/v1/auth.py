from typing import Annotated

from fastapi import APIRouter, Depends
from redis import Redis
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.redis import get_redis
from app.models.user import User
from app.schemas.auth import LoginRequest, PhoneRequest, TokenData
from app.schemas.common import ApiResponse
from app.schemas.user import UserRead, UserUpdate
from app.services.auth_service import AuthService
from app.services.sms_service import SmsService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/sms-codes", response_model=ApiResponse[None])
def send_sms_code(
    payload: PhoneRequest,
    redis_client: Annotated[Redis, Depends(get_redis)],
) -> ApiResponse[None]:
    SmsService(redis_client).send_code(payload.phone)
    return ApiResponse(message="验证码已发送")


@router.post("/login", response_model=ApiResponse[TokenData])
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
    redis_client: Annotated[Redis, Depends(get_redis)],
) -> ApiResponse[TokenData]:
    SmsService(redis_client).verify_code(payload.phone, payload.code)
    token_data = AuthService(db).login_or_register(payload.phone)
    return ApiResponse(data=token_data)


@router.get("/me", response_model=ApiResponse[UserRead])
def read_me(current_user: Annotated[User, Depends(get_current_user)]) -> ApiResponse[UserRead]:
    return ApiResponse(data=current_user)


@router.patch("/me", response_model=ApiResponse[UserRead])
def update_me(
    payload: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[UserRead]:
    current_user.nickname = payload.nickname
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return ApiResponse(data=current_user)
