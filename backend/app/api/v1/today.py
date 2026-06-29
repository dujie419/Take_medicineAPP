from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.today import TodayResponse
from app.services import today_service

router = APIRouter(prefix="/today", tags=["今日提醒"])


@router.get("", response_model=ApiResponse[TodayResponse])
def get_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[TodayResponse]:
    return ApiResponse(data=today_service.get_today(db, current_user))
