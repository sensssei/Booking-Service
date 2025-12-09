from datetime import datetime, timedelta
import jwt
import os

# Секрет и алгоритм для JWT
JWT_SECRET = os.getenv("JWT_SECRET", "change_this_secret")
JWT_ALGORITHM = "HS256"

def decode_access_token(token: str) -> int | None:
    """
    Декодирует JWT токен и возвращает user_id.
    Возвращает None, если токен недействителен или истёк.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
