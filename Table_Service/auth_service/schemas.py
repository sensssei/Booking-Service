from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """
    Схема данных для регистрации нового пользователя.
    """
    email: EmailStr
    password: constr(min_length=6)
    full_name: Optional[str] = None
    phone: Optional[str] = None

class UserLogin(BaseModel):
    """
    Схема данных для входа пользователя.
    """
    email: EmailStr
    password: str

class UserRead(BaseModel):
    """
    Данные, которые возвращаются клиенту.
    Пароль не включается никогда.
    """
    id: int
    email: EmailStr
    full_name: Optional[str]
    phone: Optional[str]
    created_at: datetime
    updated_at: datetime

class TokenResponse(BaseModel):
    """
    Ответ после успешной авторизации.
    """
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    """
    Полезная нагрузка токена JWT.
    """
    user_id: int
    exp: int
