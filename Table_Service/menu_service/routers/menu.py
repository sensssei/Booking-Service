from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlmodel import Session
from typing import List, Optional  
from datetime import datetime 
from crud_menu import get_all_menu_items, get_menu_item, create_menu_item, update_menu_item, delete_menu_item
from schemas import MenuItemCreate, MenuItemRead
from database import get_session
from utils import require_admin, decode_access_token  
from kafka_client import send_event

router = APIRouter(prefix="/menu", tags=["Menu"])

# -----------------------------
# GET /menu/ - публичный доступ
# -----------------------------
@router.get("/", response_model=List[MenuItemRead])
def read_menu(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """
    Получить список блюд меню.
    ДОСТУПНО ВСЕМ - без авторизации
    """
    items = get_all_menu_items(session)
    return items[skip:skip+limit]

# -----------------------------
# GET /menu/{id} - публичный доступ
# -----------------------------
@router.get("/{item_id}", response_model=MenuItemRead)
def get_menu_item_endpoint(
    item_id: int,
    session: Session = Depends(get_session)
):
    """
    Получить информацию о блюде по ID.
    ДОСТУПНО ВСЕМ - без авторизации
    """
    menu_item = get_menu_item(session, item_id)
    if not menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return menu_item

# -----------------------------
# POST /menu/ - только для администраторов 
# -----------------------------
@router.post("/", response_model=MenuItemRead, status_code=status.HTTP_201_CREATED)
async def add_menu_item(
    item: MenuItemCreate,
    authorization: Optional[str] = Header(None, description="Bearer token"),  
    session: Session = Depends(get_session),
):
    """
    Создать новое блюдо в меню.
    
    ТРЕБУЕТСЯ АВТОРИЗАЦИЯ:
    - Используйте кнопку 'Authorize' вверху справа в Swagger
    - Введите: Bearer <ваш_токен>
    - Или отправьте заголовок: Authorization: Bearer <token>
    
    Требуется роль: admin
    """
    # Проверяем наличие заголовка
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,  
            detail="Требуется авторизация. Используйте Authorization: Bearer <token>"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный формат токена. Должно быть: Bearer <ваш_токен>"
        )
    
    token = authorization.replace("Bearer ", "")
    
    # Проверяем, что пользователь - администратор
    user_data = require_admin(token)
    
    # Создаем блюдо
    menu_item = create_menu_item(session, item.name, item.description, item.price)
    
    # Публикуем событие в Kafka
    await send_event("menu.events", {
        "event_type": "menu_item.created",
        "item_id": menu_item.id,
        "name": menu_item.name,
        "price": menu_item.price,
        "created_by": user_data["user_id"],
        "created_at": menu_item.created_at.isoformat(),
        "service": "menu_service"
    })
    
    return menu_item

# -----------------------------
# PUT /menu/{id} - только для администраторов 
# -----------------------------
@router.put("/{item_id}", response_model=MenuItemRead)
async def update_menu_item_endpoint(
    item_id: int,
    item: MenuItemCreate,
    authorization: Optional[str] = Header(None, description="Bearer token"), 
    session: Session = Depends(get_session),
):
    """
    Обновить информацию о блюде.
    
    ТРЕБУЕТСЯ АВТОРИЗАЦИЯ:
    - Используйте кнопку 'Authorize' вверху справа
    - Введите: Bearer <ваш_токен>
    
    Требуется роль: admin
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный формат токена"
        )
    
    token = authorization.replace("Bearer ", "")
    
    # Проверяем права администратора
    user_data = require_admin(token)
    
    # Проверяем существование блюда
    existing_item = get_menu_item(session, item_id)
    if not existing_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    # Обновляем блюдо
    updated_item = update_menu_item(session, existing_item, item.name, item.description, item.price)
    
    # Публикуем событие в Kafka
    await send_event("menu.events", {
        "event_type": "menu_item.updated",
        "item_id": updated_item.id,
        "name": updated_item.name,
        "price": updated_item.price,
        "updated_by": user_data["user_id"],
        "updated_at": updated_item.updated_at.isoformat(),
        "service": "menu_service"
    })
    
    return updated_item

# -----------------------------
# DELETE /menu/{id} - только для администраторов 
# -----------------------------
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item_endpoint(
    item_id: int,
    authorization: Optional[str] = Header(None, description="Bearer token"),  
    session: Session = Depends(get_session),
):
    """
    Удалить блюдо из меню.
    
     ТРЕБУЕТСЯ АВТОРИЗАЦИЯ:
    - Используйте кнопку 'Authorize' вверху справа
    - Введите: Bearer <ваш_токен>
    
     Требуется роль: admin
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный формат токена"
        )
    
    token = authorization.replace("Bearer ", "")
    
    # Проверяем права администратора
    user_data = require_admin(token)
    
    # Проверяем существование блюда
    existing_item = get_menu_item(session, item_id)
    if not existing_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    # Удаляем блюдо
    delete_menu_item(session, existing_item)
    
    # Публикуем событие в Kafka
    await send_event("menu.events", {
        "event_type": "menu_item.deleted",
        "item_id": item_id,
        "deleted_by": user_data["user_id"],
        "deleted_at": datetime.utcnow().isoformat(),
        "service": "menu_service"
    })
    
    return None  # 204 No Content