from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MenuItemCreate(BaseModel):
    """
    Схема для создания нового блюда.
    """
    name: str
    description: Optional[str] = None
    price: float

class MenuItemRead(BaseModel):
    """
    Схема для чтения данных блюда.
    """
    id: int
    name: str
    description: Optional[str]
    price: float
    created_at: datetime
    updated_at: datetime
