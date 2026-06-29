from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.medicine import Medicine
from app.schemas.medicine import MedicineCreate


class MedicineService:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user(self, user_id: int) -> list[Medicine]:
        statement = select(Medicine).where(Medicine.user_id == user_id).order_by(Medicine.created_at.desc())
        return list(self.db.scalars(statement).all())

    def create_for_user(self, user_id: int, payload: MedicineCreate) -> Medicine:
        medicine = Medicine(user_id=user_id, **payload.model_dump())
        self.db.add(medicine)
        self.db.commit()
        self.db.refresh(medicine)
        return medicine

    def create_many_for_user(self, user_id: int, payloads: list[MedicineCreate]) -> list[Medicine]:
        medicines = [Medicine(user_id=user_id, **payload.model_dump()) for payload in payloads]
        self.db.add_all(medicines)
        self.db.commit()
        for medicine in medicines:
            self.db.refresh(medicine)
        return medicines

    def get_for_user(self, medicine_id: int, user_id: int) -> Medicine:
        statement = select(Medicine).where(Medicine.id == medicine_id, Medicine.user_id == user_id)
        medicine = self.db.scalar(statement)
        if medicine is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="药品不存在")
        return medicine
