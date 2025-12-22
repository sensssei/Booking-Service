from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import get_session
from schemas import UserCreate, UserRead, TokenResponse, UserUpdate
from crud_auth import get_user_by_email, create_user, get_user_by_id, get_all_users
from utils import verify_password, create_access_token, get_current_user, require_admin, update_user_role
from models import User
from kafka_client import send_event
from typing import List

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# -----------------------------
# Регистрация нового пользователя
# -----------------------------
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: Session = Depends(get_session)): 
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Email already exists")
    
    user = create_user(
        db, 
        payload.email, 
        payload.password, 
        payload.full_name, 
        payload.phone,
        payload.role
    )
    
    await send_event(  
        "user.events",  # Используем топик
        {
            "event_type": "user.registered",
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
            "service": "auth_service"
        }
    )
    
    return UserRead(
        id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name,
        phone=user.phone,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

# -----------------------------
# Логин пользователя
# -----------------------------
@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(user.id, user.role)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        role=user.role,
        expires_in=7200  # 2 часа
    )

# -----------------------------
# Получение данных текущего пользователя
# -----------------------------
@router.get("/me", response_model=UserRead)
def me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_session)):
    user_data = get_current_user(token, db)
    
    user = get_user_by_id(db, user_data["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserRead(
        id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name,
        phone=user.phone,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

# -----------------------------
# Админские эндпоинты
# -----------------------------

# Получение всех пользователей (только для админов)
@router.get("/users", response_model=List[UserRead])
def get_users(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100
):
    require_admin(token)  # Проверяем права администратора
    
    users = get_all_users(db, skip=skip, limit=limit)
    return [
        UserRead(
            id=user.id,
            email=user.email,
            role=user.role,
            full_name=user.full_name,
            phone=user.phone,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        for user in users
    ]

# Получение пользователя по ID (только для админов)
@router.get("/users/{user_id}", response_model=UserRead)
def get_user_by_id_endpoint(
    user_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session)
):
    require_admin(token)
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserRead(
        id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name,
        phone=user.phone,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

# Обновление роли пользователя (только для админов)
@router.patch("/users/{user_id}/role", response_model=UserRead)
def update_user_role_endpoint(
    user_id: int,
    role_update: UserUpdate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session)
):
    require_admin(token)
    
    if not role_update.role:
        raise HTTPException(status_code=400, detail="Role is required")
    
    user = update_user_role(user_id, role_update.role, db)
    
    return UserRead(
        id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name,
        phone=user.phone,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

# -----------------------------
# Проверка токена
# -----------------------------
@router.post("/verify")
def verify_token_endpoint(token: str = Depends(oauth2_scheme)):
    from utils import verify_token
    is_valid = verify_token(token)
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {"valid": True, "message": "Token is valid"}