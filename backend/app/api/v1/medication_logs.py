from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.medication_log import MedicationLogHistoryResponse
from app.schemas.today import MedicationLogCreate, TodayItem
from app.services import medication_log_service, today_service

router = APIRouter(prefix="/medication-logs", tags=["服药记录"])


@router.get("", response_model=ApiResponse[MedicationLogHistoryResponse])
def get_medication_logs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[MedicationLogHistoryResponse]:
    return ApiResponse(
        data=medication_log_service.get_history(
            db,
            current_user,
            limit=limit,
            offset=offset,
        )
    )


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
