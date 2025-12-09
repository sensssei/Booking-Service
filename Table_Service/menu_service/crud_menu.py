from sqlmodel import Session, select
from models import MenuItem
from datetime import datetime
from typing import Optional, List

def get_all_menu_items(session: Session) -> List[MenuItem]:
    statement = select(MenuItem)
    result = session.execute(statement)
    return result.scalars().all()

def get_menu_item(session: Session, item_id: int) -> Optional[MenuItem]:
    statement = select(MenuItem).where(MenuItem.id == item_id)
    result = session.execute(statement)
    return result.scalar_one_or_none()

def create_menu_item(session: Session, name: str, description: Optional[str], price: float) -> MenuItem:
    item = MenuItem(name=name, description=description, price=price)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

def update_menu_item(session: Session, item: MenuItem, name: str, description: Optional[str], price: float) -> MenuItem:
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