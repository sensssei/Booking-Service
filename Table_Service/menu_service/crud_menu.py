from sqlmodel import Session, select
from models import MenuItem
from datetime import datetime

def get_all_menu_items(session: Session):
    return session.exec(select(MenuItem)).all()

def get_menu_item(session: Session, item_id: int):
    return session.exec(select(MenuItem).where(MenuItem.id == item_id)).first()

def create_menu_item(session: Session, name: str, description: str | None, price: float):
    item = MenuItem(name=name, description=description, price=price)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

def update_menu_item(session: Session, item: MenuItem, name: str, description: str | None, price: float):
    item.name = name
    item.description = description
    item.price = price
    item.updated_at = datetime.utcnow()
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

def delete_menu_item(session: Session, item: MenuItem):
    session.delete(item)
    session.commit()