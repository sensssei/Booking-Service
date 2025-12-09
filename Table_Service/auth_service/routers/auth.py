from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import get_session
from schemas import UserCreate, UserRead, TokenResponse
from crud_auth import get_user_by_email, create_user
from utils import verify_password, create_access_token, decode_access_token
from models import User
from kafka_client import send_event
import asyncio

# Создаём router для FastAPI
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Получение сессии БД
def get_db():
       yield from get_session()

# -----------------------------
# Регистрация нового пользователя
# -----------------------------
# Публикуем событие user.registered

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Email already exists")
    
    user = create_user(db, payload.email, payload.password, payload.full_name, payload.phone)
    
    # Публикуем событие user.registered в Kafka
    asyncio.create_task(send_event(
        "user.registered",
        {
            "uuid": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone
        }
    ))
    
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


# -----------------------------
# Логин пользователя
# -----------------------------
@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)

# -----------------------------
# Получение данных текущего пользователя
# -----------------------------
@router.get("/me", response_model=UserRead)
def me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
