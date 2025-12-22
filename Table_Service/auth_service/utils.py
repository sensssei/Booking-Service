from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
import os
import bcrypt
from fastapi import HTTPException
from sqlmodel import Session, select
from models import User
from typing import Optional, Dict, Any

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройки JWT с ассиметричными ключами
JWT_PRIVATE_KEY_PATH = os.getenv("JWT_PRIVATE_KEY_PATH", "private_key.pem")
JWT_PUBLIC_KEY_PATH = os.getenv("JWT_PUBLIC_KEY_PATH", "public_key.pem")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))  # 2 часа

# Загружаем ключи
try:
    with open(JWT_PRIVATE_KEY_PATH, 'r') as f:
        JWT_PRIVATE_KEY = f.read()
    
    with open(JWT_PUBLIC_KEY_PATH, 'r') as f:
        JWT_PUBLIC_KEY = f.read()
except FileNotFoundError as e:
    print(f"⚠️  Warning: Key file not found: {e}")
    print("⚠️  Using fallback HS256 with default secret")
    JWT_PRIVATE_KEY = os.getenv("JWT_SECRET", "change_this_secret")
    JWT_PUBLIC_KEY = JWT_PRIVATE_KEY
    JWT_ALGORITHM = "HS256"

# -----------------------------
# Функции для паролей
# -----------------------------
def get_password_hash(password: str) -> str:
    """Хеширование пароля с использованием bcrypt"""
    if not password:
        raise ValueError("Password cannot be empty")
    
    truncated = password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(truncated, bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля с использованием bcrypt"""
    if not plain_password or not hashed_password:
        return False
    
    try:
        truncated = plain_password.encode("utf-8")[:72]
        return bcrypt.checkpw(truncated, hashed_password.encode("utf-8"))
    except Exception:
        return False

# -----------------------------
# Функции для JWT с ассиметричными ключами
# -----------------------------
def create_access_token(user_id: int, role: str = "user", expires_delta_minutes: int = None) -> str:
    """
    Создаёт JWT токен для пользователя с ролью
    Использует приватный ключ (только auth_service может создавать токены)
    """
    if expires_delta_minutes is None:
        expires_delta_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
    
    expire = datetime.utcnow() + timedelta(minutes=expires_delta_minutes)
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),  # issued at
        "iss": "auth_service",  # issuer для проверки
        "aud": "restaurant_services"  # audience
    }
    
    # Используем приватный ключ для подписи (RS256) или симметричный ключ (HS256)
    token = jwt.encode(payload, JWT_PRIVATE_KEY, algorithm=JWT_ALGORITHM)
    return token

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Декодирует JWT токен и возвращает словарь с user_id и role
    Использует публичный ключ для проверки подписи (RS256)
    """
    try:
        # Для RS256 используем публичный ключ, для HS256 - тот же секрет
        key = JWT_PUBLIC_KEY if JWT_ALGORITHM == "RS256" else JWT_PUBLIC_KEY
        
        payload = jwt.decode(
            token, 
            key, 
            algorithms=[JWT_ALGORITHM],
            issuer="auth_service" if JWT_ALGORITHM == "RS256" else None,
            audience="restaurant_services" if JWT_ALGORITHM == "RS256" else None
        )
        
        # Преобразуем exp из datetime обратно в timestamp для проверки
        if isinstance(payload.get("exp"), datetime):
            if payload["exp"] < datetime.utcnow():
                return None
        
        return {
            "user_id": payload.get("user_id"),
            "role": payload.get("role", "user"),
            "exp": payload.get("exp"),
            "iss": payload.get("iss"),
            "aud": payload.get("aud")
        }
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError as e:
        print(f"Token validation error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error decoding token: {e}")
        return None

def get_current_user(token: str, db: Session) -> Dict[str, Any]:
    """
    Получает текущего пользователя по токену
    """
    payload = decode_access_token(token)
    
    if not payload or not payload.get("user_id"):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    statement = select(User).where(User.id == payload["user_id"])
    user = db.execute(statement).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name,
        "phone": user.phone,
        "created_at": user.created_at
    }

def verify_token(token: str) -> bool:
    """
    Простая проверка валидности токена
    """
    return decode_access_token(token) is not None

def get_user_id_from_token(token: str) -> Optional[int]:
    """
    Извлекает user_id из токена
    """
    payload = decode_access_token(token)
    return payload.get("user_id") if payload else None

def get_user_role_from_token(token: str) -> Optional[str]:
    """
    Извлекает роль пользователя из токена
    """
    payload = decode_access_token(token)
    return payload.get("role") if payload else None

# -----------------------------
# Функции для проверки прав доступа
# -----------------------------
def require_admin(token: str) -> Dict[str, Any]:
    """
    Проверяет, что пользователь имеет роль администратора
    """
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    return payload

def require_role(token: str, required_role: str) -> Dict[str, Any]:
    """
    Проверяет, что пользователь имеет определенную роль
    """
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if payload.get("role") != required_role:
        raise HTTPException(
            status_code=403,
            detail=f"{required_role.capitalize()} access required"
        )
    
    return payload

def has_role(token: str, required_role: str) -> bool:
    """
    Проверяет, имеет ли пользователь определенную роль
    """
    try:
        require_role(token, required_role)
        return True
    except HTTPException:
        return False

# -----------------------------
# Функции для обновления модели User
# -----------------------------
def update_user_role(user_id: int, new_role: str, db: Session) -> User:
    """
    Обновляет роль пользователя
    """
    statement = select(User).where(User.id == user_id)
    user = db.execute(statement).scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = new_role
    user.updated_at = datetime.utcnow()
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

# -----------------------------
# Хелпер для создания начального администратора
# -----------------------------
def create_default_admin(db: Session):
    """
    Создает администратора по умолчанию, если его нет
    """
    from models import User
    
    admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@restaurant.com")
    admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin123!")
    
    statement = select(User).where(User.email == admin_email)
    existing_admin = db.execute(statement).scalar_one_or_none()
    
    if not existing_admin:
        admin_user = User(
            email=admin_email,
            password_hash=get_password_hash(admin_password),
            full_name="System Administrator",
            role="admin"
        )
        
        db.add(admin_user)
        db.commit()
        print(f" Created default admin user: {admin_email}")
    else:
        print(f" Admin user already exists: {admin_email}")