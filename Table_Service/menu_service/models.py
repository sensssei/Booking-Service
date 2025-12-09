from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class MenuItem(SQLModel, table=True):
    """
    ORM-модель для таблицы блюд.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False, index=True)
    description: Optional[str] = None
    price: float = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
