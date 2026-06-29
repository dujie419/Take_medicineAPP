from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.medicine import MedicineBatchCreate, MedicineCreate, MedicineRecognitionRead, MedicineRead
from app.services.ai_recognition_service import AiRecognitionService
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


@router.post("/batch", response_model=ApiResponse[list[MedicineRead]])
def batch_create_medicines(
    payload: MedicineBatchCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[MedicineRead]]:
    medicines = MedicineService(db).create_many_for_user(current_user.id, payload.medicines)
    return ApiResponse(data=medicines)


@router.post("/recognize", response_model=ApiResponse[MedicineRecognitionRead])
async def recognize_medicine_image(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: Annotated[UploadFile, File(...)],
) -> ApiResponse[MedicineRecognitionRead]:
    record, result = await AiRecognitionService(db).recognize(current_user.id, file)
    data = MedicineRecognitionRead(
        record_id=record.id,
        image_path=record.image_path,
        recognition_mode=record.recognition_mode,
        **result.model_dump(),
    )
    return ApiResponse(data=data)


@router.get("/{medicine_id}", response_model=ApiResponse[MedicineRead])
def read_medicine(
    medicine_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[MedicineRead]:
    medicine = MedicineService(db).get_for_user(medicine_id, current_user.id)
    return ApiResponse(data=medicine)
