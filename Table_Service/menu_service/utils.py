import jwt
import os
from fastapi import HTTPException, status

JWT_SECRET = os.getenv("JWT_SECRET", "change_this_secret")
JWT_ALGORITHM = "HS256"

def decode_access_token(token: str) -> dict:
    """
    Декодирует JWT токен и возвращает словарь с user_id и role.
    Совместимо с auth_service.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Получаем user_id и role из токена
        user_id = payload.get("user_id")
        role = payload.get("role", "user")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        return {
            "user_id": user_id,
            "role": role
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation error: {str(e)}"
        )

def require_admin(token: str) -> dict:
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

def require_role(token: str, required_role: str) -> dict:
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