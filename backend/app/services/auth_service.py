from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import TokenData


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def login_or_register(self, phone: str) -> TokenData:
        user = self.db.scalar(select(User).where(User.phone == phone))
        if user is None:
            user = User(phone=phone, nickname=f"用户{phone[-4:]}", timezone="Asia/Shanghai")
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被停用")

        token = create_access_token(user.id)
        return TokenData(access_token=token, user=user)
