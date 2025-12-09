import jwt
import os
from fastapi import HTTPException, status, Header
from typing import Optional, Dict, Any

JWT_SECRET = os.getenv("JWT_SECRET", "change_this_secret")
JWT_ALGORITHM = "HS256"

def decode_jwt_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
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

# Функция для работы с Swagger
async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Dependency для получения текущего пользователя.
    Совместимо со Swagger авторизацией.
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required. Use 'Bearer <token>'"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'"
        )
    
    token = authorization[7:]  
    return decode_jwt_token(token)

def require_admin(token: str) -> Dict[str, Any]:
    """
    Проверяет, что пользователь имеет роль администратора.
    Возвращает данные пользователя из токена.
    """
    user_data = decode_jwt_token(token)
    
    if user_data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user_data