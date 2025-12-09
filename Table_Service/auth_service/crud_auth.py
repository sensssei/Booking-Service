from sqlmodel import Session, select
from models import User
from utils import get_password_hash

# Поиск пользователя по email
def get_user_by_email(session: Session, email: str):
    return session.exec(select(User).where(User.email == email)).first()

# Поиск пользователя по id
def get_user_by_id(session: Session, user_id: int):
    return session.exec(select(User).where(User.id == user_id)).first()

# Создание нового пользователя
def create_user(session: Session, email: str, password: str, full_name: str | None = None, phone: str | None = None):
    user = User(
        email=email,
        password_hash=get_password_hash(password),
        full_name=full_name or "",
        phone=phone or ""
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
