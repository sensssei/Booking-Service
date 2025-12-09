from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class ReservationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class ReservationCreate(BaseModel):
    table_id: int
    guests_count: int = Field(ge=1, le=20, description="Количество гостей (1-20)")
    reservation_time: datetime = Field(description="Дата и время бронирования")
    duration_minutes: int = Field(default=120, ge=30, le=360, description="Продолжительность в минутах (30-360)")
    contact_phone: str = Field(description="Контактный телефон")
    contact_email: EmailStr = Field(description="Email для подтверждения")
    special_requests: Optional[str] = Field(None, description="Особые пожелания")


class ReservationRead(BaseModel):
    id: int
    reservation_code: str
    user_id: int
    table_id: int
    guests_count: int
    reservation_time: datetime
    duration_minutes: int
    status: ReservationStatus
    contact_phone: str
    contact_email: str
    special_requests: Optional[str]
    created_at: datetime

class TableRead(BaseModel):
    """Схема для чтения информации о столе"""
    id: int
    table_number: int
    capacity: int
    description: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AvailableTablesRequest(BaseModel):
    """Запрос на поиск доступных столов"""
    guests: int = Field(ge=1, le=20)
    start_time: datetime
    duration_minutes: int = Field(default=120, ge=30, le=360)

class CancelReservationRequest(BaseModel):
    """Запрос на отмену бронирования"""
    reason: Optional[str] = None

class ReservationUpdate(BaseModel):
    """Схема для обновления бронирования"""
    guests_count: Optional[int] = Field(None, ge=1, le=20)
    reservation_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=30, le=360)
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    special_requests: Optional[str] = None