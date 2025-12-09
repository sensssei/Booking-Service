from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
from crud_menu import get_all_menu_items, get_menu_item, create_menu_item, update_menu_item, delete_menu_item
from schemas import MenuItemCreate, MenuItemRead
from database import get_session
from utils import decode_access_token
from kafka import KafkaProducer
import os
import json

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

router = APIRouter(prefix="/menu", tags=["Menu"])

# -----------------------------
# Helper для проверки роли admin
# -----------------------------
def require_admin(token: str):
    user_id = decode_access_token(token)
    # TODO: проверить роль пользователя по user_id (здесь заглушка)
    if user_id != 1:  # пример: user_id=1 — админ
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id

# -----------------------------
# GET /menu/
# -----------------------------
@router.get("/", response_model=List[MenuItemRead])
def read_menu(session: Session = Depends(get_session)):
    return get_all_menu_items(session)

# -----------------------------
# POST /menu/
# -----------------------------
@router.post("/", response_model=MenuItemRead, status_code=status.HTTP_201_CREATED)
def add_menu_item(item: MenuItemCreate, token: str = Depends(), session: Session = Depends(get_session)):
    require_admin(token)
    menu_item = create_menu_item(session, item.name, item.description, item.price)
    # Публикация события
    producer.send("menu_events", {"event": "created", "item_id": menu_item.id, "name": menu_item.name})
    return menu_item

# -----------------------------
# PUT /menu/{id}
# -----------------------------
@router.put("/{item_id}", response_model=MenuItemRead)
def update_menu(item_id: int, item: MenuItemCreate, token: str = Depends(), session: Session = Depends(get_session)):
    require_admin(token)
    existing_item = get_menu_item(session, item_id)
    if not existing_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    updated_item = update_menu_item(session, existing_item, item.name, item.description, item.price)
    producer.send("menu_events", {"event": "updated", "item_id": updated_item.id, "name": updated_item.name})
    return updated_item

# -----------------------------
# DELETE /menu/{id}
# -----------------------------
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu(item_id: int, token: str = Depends(), session: Session = Depends(get_session)):
    require_admin(token)
    existing_item = get_menu_item(session, item_id)
    if not existing_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    delete_menu_item(session, existing_item)
    producer.send("menu_events", {"event": "deleted", "item_id": item_id})
    return {"detail": "Menu item deleted"}
