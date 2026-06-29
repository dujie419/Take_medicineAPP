from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.today import MedicationLogCreate, TodayItem
from app.services import today_service

router = APIRouter(prefix="/medication-logs", tags=["服药操作"])


@router.post("", response_model=ApiResponse[TodayItem])
def record_medication_action(
    payload: MedicationLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        item = today_service.record_group_action(db, current_user, payload)
    except today_service.ReminderGroupNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"code": 40403, "message": "今日提醒组不存在", "data": None},
        )
    return ApiResponse(data=item, message="服药状态已更新")
