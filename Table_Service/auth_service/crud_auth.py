from sqlmodel import Session, select
from models import User
from utils import get_password_hash

def get_user_by_email(session: Session, email: str):
    statement = select(User).where(User.email == email)
    result = session.execute(statement)
    return result.scalar_one_or_none()

def get_user_by_id(session: Session, user_id: int):
    statement = select(User).where(User.id == user_id)
    result = session.execute(statement)
    return result.scalar_one_or_none()

def create_user(session: Session, email: str, password: str, full_name: str | None = None, phone: str | None = None, role: str = "user"):
    user = User(
        email=email,
        password_hash=get_password_hash(password),
        full_name=full_name or "",
        phone=phone or "",
        role=role
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def get_all_users(session: Session, skip: int = 0, limit: int = 100):
    statement = select(User).offset(skip).limit(limit)
    result = session.execute(statement)
    return result.scalars().all()