from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.medicine import MedicineCreate, MedicineRead
from app.services.medicine_service import MedicineService


router = APIRouter(prefix="/medicines", tags=["medicines"])


@router.get("", response_model=ApiResponse[list[MedicineRead]])
def list_medicines(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[MedicineRead]]:
    medicines = MedicineService(db).list_by_user(current_user.id)
    return ApiResponse(data=medicines)


@router.post("", response_model=ApiResponse[MedicineRead])
def create_medicine(
    payload: MedicineCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[MedicineRead]:
    medicine = MedicineService(db).create_for_user(current_user.id, payload)
    return ApiResponse(data=medicine)


@router.get("/{medicine_id}", response_model=ApiResponse[MedicineRead])
def read_medicine(
    medicine_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[MedicineRead]:
    medicine = MedicineService(db).get_for_user(medicine_id, current_user.id)
    return ApiResponse(data=medicine)
