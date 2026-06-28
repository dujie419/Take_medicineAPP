from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.plan import PlanCreate, PlanUpdate
from app.services import plan_service

router = APIRouter(prefix="/plans", tags=["用药计划"])


def _success(data=None, message: str = "success", status_code: int = 200):
    return JSONResponse(
        status_code=status_code,
        content={"code": 0, "message": message, "data": data},
    )


def _error(status_code: int, code: int, message: str):
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message, "data": None},
    )


@router.get("")
def list_medication_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = plan_service.list_plans(db, current_user.id)
    return _success(
        {
            "items": [item.model_dump(mode="json") for item in items],
            "total": len(items),
        }
    )


@router.post("")
def create_medication_plan(
    payload: PlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        plan = plan_service.create_plan(db, payload, current_user.id)
    except plan_service.MedicineNotFoundError:
        return _error(status.HTTP_404_NOT_FOUND, 40401, "药品不存在")
    return _success(
        plan.model_dump(mode="json"),
        message="用药计划创建成功",
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/{plan_id}")
def get_medication_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        plan = plan_service.get_plan(db, plan_id, current_user.id)
    except plan_service.PlanNotFoundError:
        return _error(status.HTTP_404_NOT_FOUND, 40402, "用药计划不存在")
    return _success(plan.model_dump(mode="json"))


@router.patch("/{plan_id}")
def update_medication_plan(
    plan_id: int,
    payload: PlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        plan = plan_service.update_plan(db, plan_id, payload, current_user.id)
    except plan_service.PlanNotFoundError:
        return _error(status.HTTP_404_NOT_FOUND, 40402, "用药计划不存在")
    except ValueError as exc:
        return _error(status.HTTP_422_UNPROCESSABLE_ENTITY, 42201, str(exc))
    return _success(plan.model_dump(mode="json"), message="用药计划更新成功")


@router.delete("/{plan_id}")
def delete_medication_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        plan_service.delete_plan(db, plan_id, current_user.id)
    except plan_service.PlanNotFoundError:
        return _error(status.HTTP_404_NOT_FOUND, 40402, "用药计划不存在")
    return _success(message="用药计划删除成功")
