from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class User(SQLModel, table=True):
    """
    ORM-модель таблицы пользователей.
    Соответствует структуре базы данных.
    """
    id: Optional[int] = Field(default=None, primary_key=True)

    email: str = Field(index=True, nullable=False, unique=True)
    password_hash: str = Field(nullable=False)
    
    # Добавляем поле role
    role: str = Field(default="user", nullable=False)  # "user", "admin", "manager"

    full_name: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)