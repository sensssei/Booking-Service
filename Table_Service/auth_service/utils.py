from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
import os
import bcrypt

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Секрет и алгоритм для JWT
JWT_SECRET = os.getenv("JWT_SECRET", "change_this_secret")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # 2 часа

# -----------------------------
# Функции для паролей
# -----------------------------
def get_password_hash(password: str) -> str:
    if password is None:
        password = ""
    truncated = password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(truncated, bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    truncated = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(truncated, hashed_password.encode("utf-8"))

# -----------------------------
# Функции для JWT
# -----------------------------
def create_access_token(user_id: int, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    """
    Создаёт JWT токен для пользователя
    """
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    payload = {
        "user_id": user_id,
        "exp": expire.timestamp()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def decode_access_token(token: str) -> int | None:
    """
    Декодирует JWT токен и возвращает user_id
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
