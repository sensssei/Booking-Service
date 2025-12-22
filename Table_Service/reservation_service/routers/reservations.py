from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from database import get_session
from schemas import ReservationCreate, ReservationRead
from crud_reservation import create_reservation, get_user_reservations
from utils import get_current_user, require_admin

router = APIRouter(prefix="/reservations", tags=["Reservations"])

@router.post("/", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
async def create_new_reservation(
    reservation: ReservationCreate,
    authorization: Optional[str] = Header(None, description="Bearer token"),
    session: Session = Depends(get_session)
):
    """
    Создать новое бронирование столика.
    
     ТРЕБУЕТСЯ АВТОРИЗАЦИЯ:
    - Используйте кнопку 'Authorize' вверху справа
    - Введите: Bearer <ваш_токен>
    
     Параметры бронирования:
    - table_id: ID столика
    - guests_count: количество гостей (1-20)
    - reservation_time: дата и время бронирования
    - duration_minutes: продолжительность (30-360 минут)
    - contact_phone: контактный телефон
    - contact_email: email для подтверждения
    - special_requests: особые пожелания (опционально)
    """
    # Проверяем наличие заголовка авторизации
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация. Используйте Authorization: Bearer <token>"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный формат токена. Должно быть: Bearer <ваш_токен>"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Получаем пользователя из токена
        from utils import decode_jwt_token
        user_data = decode_jwt_token(token)
        user_id = user_data["user_id"]
        
        # ДОБАВЛЯЕМ ЛОГГИРОВАНИЕ ДЛЯ ОТЛАДКИ
        print(f" Creating reservation for user {user_id}")
        print(f"   Table ID: {reservation.table_id}")
        print(f"   Guests: {reservation.guests_count}")
        print(f"   Time: {reservation.reservation_time}")
        
        # Создаем бронирование
        new_reservation = create_reservation(
            session=session,
            user_id=user_id,
            data=reservation
        )
        
        # Отправляем событие в Kafka 
        try:
            from kafka_client import send_reservation_event
            await send_reservation_event("reservation.created", {
                "id": new_reservation.id,
                "reservation_code": new_reservation.reservation_code,
                "user_id": user_id,
                "table_id": new_reservation.table_id,
                "guests_count": new_reservation.guests_count,
                "reservation_date": new_reservation.reservation_time,
                "status": new_reservation.status.value,
                "service": "reservation_service"
            })
        except Exception as kafka_error:
            print(f" Kafka error (non-critical): {kafka_error}")
        
        print(f" Reservation created: {new_reservation.reservation_code}")
        
        return new_reservation
        
    except ValueError as e:
        print(f" Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f" CRITICAL ERROR creating reservation: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()  # Выводим полный стек трейс
        raise HTTPException(status_code=500, detail=f"Internal server error: {type(e).__name__}")

@router.get("/my", response_model=List[ReservationRead])
def get_my_reservations(
    authorization: Optional[str] = Header(None, description="Bearer token"),
    session: Session = Depends(get_session)
):
    """
    Получить список моих бронирований.
    
     ТРЕБУЕТСЯ АВТОРИЗАЦИЯ:
    - Используйте кнопку 'Authorize' вверху справа
    - Введите: Bearer <ваш_токен>
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный формат токена"
        )
    
    token = authorization.replace("Bearer ", "")
    
    from utils import decode_jwt_token
    user_data = decode_jwt_token(token)
    user_id = user_data["user_id"]
    
    return get_user_reservations(session, user_id)

@router.get("/", response_model=List[ReservationRead])
def get_all_reservations(
    authorization: Optional[str] = Header(None, description="Bearer token (admin only)"),
    session: Session = Depends(get_session)
):
    """
    Получить все бронирования (только для администраторов).
    
     ТРЕБУЕТСЯ АВТОРИЗАЦИЯ:
    - Используйте кнопку 'Authorize' вверху справа
    - Введите: Bearer <ваш_токен>
    
     Требуется роль: admin
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный формат токена"
        )
    
    token = authorization.replace("Bearer ", "")
    
    # Проверяем права администратора
    from utils import require_admin
    user_data = require_admin(token)
    
    
    from models import Reservation
    result = session.execute(select(Reservation))
    reservations = result.scalars().all()
    return reservations

@router.get("/tables/available")
def get_available_tables_endpoint(
    guests: int,
    start_time: datetime,
    duration_minutes: int = 120,
    authorization: Optional[str] = Header(None, description="Bearer token"),
    session: Session = Depends(get_session)
):
    """
    Получить список доступных столов на указанное время.
    
     ТРЕБУЕТСЯ АВТОРИЗАЦИЯ
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный формат токена"
        )
    
    token = authorization.replace("Bearer ", "")
    
    from utils import decode_jwt_token
    user_data = decode_jwt_token(token)
    
    # Проверяем доступность столов
    from crud_reservation import get_available_tables
    try:
        available_tables = get_available_tables(session, guests, start_time, duration_minutes)
        return available_tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/code/{reservation_code}", response_model=ReservationRead)
def get_reservation_by_code_endpoint(
    reservation_code: str,
    authorization: Optional[str] = Header(None, description="Bearer token"),
    session: Session = Depends(get_session)
):
    """
    Получить информацию о бронировании по коду.
    
     ТРЕБУЕТСЯ АВТОРИЗАЦИЯ
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный формат токена"
        )
    
    token = authorization.replace("Bearer ", "")
    
    from utils import decode_jwt_token
    user_data = decode_jwt_token(token)
    
    from crud_reservation import get_reservation_by_code
    reservation = get_reservation_by_code(session, reservation_code)
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    # Проверяем права доступа
    if reservation.user_id != user_data["user_id"] and user_data["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own reservations"
        )
    
    return reservation

# ОТЛАДОЧНЫЙ ЭНДПОИНТ 
@router.get("/debug/tables")
def debug_tables(
    session: Session = Depends(get_session)
):
    """
    Отладочный эндпоинт: получить все столы.
    Не требует авторизации.
    """
    from models import Table
    
    result = session.execute(select(Table))
    tables = result.scalars().all()
    
    return {
        "count": len(tables),
        "tables": [
            {
                "id": t.id,
                "table_number": t.table_number,
                "capacity": t.capacity,
                "is_active": t.is_active,
                "description": t.description
            }
            for t in tables
        ]
    }

@router.get("/tables")
def get_all_tables_endpoint(
    session: Session = Depends(get_session)
):
    """
    Получить список всех столов.
     Публичный доступ - без авторизации
    """
    from models import Table
    
    result = session.execute(select(Table))
    tables = result.scalars().all()
    
    return [
        {
            "id": t.id,
            "table_number": t.table_number,
            "capacity": t.capacity,
            "description": t.description,
            "is_active": t.is_active,
            "created_at": t.created_at,
            "service": "reservation_service"
            
        }
        for t in tables
    ]