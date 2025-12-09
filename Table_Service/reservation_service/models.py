from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class ReservationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class Table(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    table_number: int = Field(unique=True, index=True)
    capacity: int = Field(ge=1, le=12)
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Reservation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    reservation_code: str = Field(unique=True, index=True)
    user_id: int = Field(index=True)
    table_id: int = Field(foreign_key="table.id", index=True)
    guests_count: int = Field(ge=1, le=20)
    reservation_time: datetime = Field(index=True)
    duration_minutes: int = Field(default=120)
    status: ReservationStatus = Field(default=ReservationStatus.PENDING)
    contact_phone: str = Field()
    contact_email: str = Field()
    special_requests: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)