from sqlmodel import Session, select
from datetime import datetime, timedelta
import uuid
from models import Reservation, Table, ReservationStatus
from schemas import ReservationCreate

def generate_reservation_code():
    return f"RES-{uuid.uuid4().hex[:8].upper()}"

def create_reservation(session: Session, user_id: int, data: ReservationCreate):
    print(f" CRUD: Creating reservation for user {user_id}")
    print(f"   Checking table {data.table_id}")
    
    # Проверяем стол
    table = session.get(Table, data.table_id)
    if not table:
        print(f" Table {data.table_id} not found")
        raise ValueError(f"Table {data.table_id} not found")
    
    print(f"   Table found: #{table.table_number}, capacity: {table.capacity}")
    
    if not table.is_active:
        print(f" Table {table.table_number} is not active")
        raise ValueError(f"Table #{table.table_number} is not active")
    
    if data.guests_count > table.capacity:
        print(f" Too many guests: {data.guests_count} > {table.capacity}")
        raise ValueError(f"Table capacity is {table.capacity} guests")
    
    # Проверяем доступность
    end_time = data.reservation_time + timedelta(minutes=data.duration_minutes)
    print(f"   Checking availability from {data.reservation_time} to {end_time}")
    
    #  получаем существующие бронирования и проверяем вручную
    statement = select(Reservation).where(
        Reservation.table_id == data.table_id,
        Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED])
    )
    
    result = session.execute(statement)
    existing_reservations = result.scalars().all()
    
    for existing_res in existing_reservations:
        existing_end = existing_res.reservation_time + timedelta(minutes=existing_res.duration_minutes)
        
        # Проверяем пересечение временных интервалов
        if (data.reservation_time < existing_end and 
            end_time > existing_res.reservation_time):
            print(f" Table already booked: conflict with reservation {existing_res.reservation_code}")
            raise ValueError(f"Table is already booked from {existing_res.reservation_time} to {existing_end}")
    
    # Создаём бронирование
    reservation_code = generate_reservation_code()
    print(f"   Creating reservation with code: {reservation_code}")
    
    reservation = Reservation(
        reservation_code=reservation_code,
        user_id=user_id,
        table_id=data.table_id,
        guests_count=data.guests_count,
        reservation_time=data.reservation_time,
        duration_minutes=data.duration_minutes,
        contact_phone=data.contact_phone,
        contact_email=data.contact_email,
        special_requests=data.special_requests,
        status=ReservationStatus.PENDING
    )
    
    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    
    print(f" Reservation created successfully: {reservation_code}")
    return reservation

def get_user_reservations(session: Session, user_id: int):
    statement = select(Reservation).where(Reservation.user_id == user_id)
    statement = statement.order_by(Reservation.reservation_time.desc())
    result = session.execute(statement)
    return result.scalars().all()

def get_reservation_by_code(session: Session, code: str):
    statement = select(Reservation).where(Reservation.reservation_code == code)
    result = session.execute(statement)
    return result.scalar_one_or_none()

def get_available_tables(session: Session, guests: int, start_time: datetime, duration_minutes: int = 120):
    """Получить доступные столы на указанное время"""
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    # Находим все занятые столы в указанный период
    statement = select(Reservation.table_id).where(
        Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED])
    )
    
    result = session.execute(statement)
    all_reservations = result.scalars().all()
    
    # Фильтруем вручную по времени
    booked_table_ids = []
    for reservation in all_reservations:
        reservation_obj = session.get(Reservation, reservation)
        if reservation_obj:
            reservation_end = reservation_obj.reservation_time + timedelta(minutes=reservation_obj.duration_minutes)
            if (start_time < reservation_end and end_time > reservation_obj.reservation_time):
                booked_table_ids.append(reservation_obj.table_id)
    
    # Находим все доступные столы нужной вместимости
    statement = select(Table).where(
        Table.is_active == True,
        Table.capacity >= guests
    )
    
    if booked_table_ids:
        statement = statement.where(Table.id.not_in(booked_table_ids))
    
    result = session.execute(statement)
    return result.scalars().all()