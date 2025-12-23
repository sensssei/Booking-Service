import jwt
import os
from fastapi import HTTPException, status
from typing import Dict, Any

# Настройки JWT с ассиметричными ключами
JWT_PUBLIC_KEY_PATH = os.getenv("JWT_PUBLIC_KEY_PATH", "public_key.pem")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")

# Загружаем публичный ключ
try:
    with open(JWT_PUBLIC_KEY_PATH, 'r') as f:
        JWT_PUBLIC_KEY = f.read()
except FileNotFoundError:
    # Fallback на HS256 для обратной совместимости
    print(f"⚠️  Warning: Public key file not found: {JWT_PUBLIC_KEY_PATH}")
    print("⚠️  Using fallback HS256")
    JWT_PUBLIC_KEY = os.getenv("JWT_SECRET", "change_this_secret")
    JWT_ALGORITHM = "HS256"

def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Декодирует JWT токен и возвращает словарь с user_id и role.
    Использует публичный ключ для проверки подписи (RS256) или секрет (HS256).
    """
    try:
        # Для RS256 проверяем issuer и audience, для HS256 - только подпись
        if JWT_ALGORITHM == "RS256":
            payload = jwt.decode(
                token, 
                JWT_PUBLIC_KEY, 
                algorithms=["RS256"],  
                issuer="auth_service",  # Проверяем, что токен выпущен auth_service
                audience="restaurant_services"  # Проверяем аудиторию
            )
        else:
            # Fallback для HS256 (обратная совместимость)
            payload = jwt.decode(
                token, 
                JWT_PUBLIC_KEY, 
                algorithms=["HS256"]  
            )
        
        # Получаем user_id и role из токена
        user_id = payload.get("user_id")
        role = payload.get("role", "user")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token: missing user_id")
            
        return {
            "user_id": user_id,
            "role": role,
            "exp": payload.get("exp")
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidIssuerError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token issuer. Token must be issued by auth_service"
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token validation error: {str(e)}"
        )

def require_admin(token: str) -> Dict[str, Any]:
    """
    Проверяет, что пользователь имеет роль администратора.
    Возвращает данные пользователя из токена.
    """
    user_data = decode_access_token(token)
    
    if user_data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user_data

def require_role(token: str, required_role: str) -> Dict[str, Any]:
    """
    Проверяет, что пользователь имеет определенную роль.
    """
    user_data = decode_access_token(token)
    
    if user_data.get("role") != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{required_role.capitalize()} access required"
        )
    
    return user_data

def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Альтернативное имя для совместимости с существующим кодом.
    """
    return decode_access_token(token)