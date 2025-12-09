import os
from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy.orm import sessionmaker
import time

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://res_user:res_pass@postgres_reservation:5432/res_db"
)

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db_and_tables():
    retries = 10
    for i in range(retries):
        try:
            SQLModel.metadata.create_all(engine)
            print("Reservation database connected and tables created!")
            
            # Создаем тестовые столы если их нет
            create_sample_tables()
            
            break
        except Exception as e:
            print(f"Reservation database not ready ({i+1}/{retries}): {e}")
            time.sleep(3)
    else:
        raise Exception("Failed to connect to reservation database after retries")

def create_sample_tables():
    """Создание тестовых столов при инициализации БД"""
    session = SessionLocal()
    try:
        # Проверяем, есть ли уже столы
        from models import Table
        
        result = session.execute(select(Table))
        tables_count = result.first()
        
        if not tables_count:
            # Создаем 10 тестовых столов
            tables = []
            for i in range(1, 11):
                table = Table(
                    table_number=i,
                    capacity=4 if i <= 5 else 6 if i <= 8 else 8,
                    description=f"Table #{i} - {'Small' if i <= 5 else 'Medium' if i <= 8 else 'Large'}"
                )
                tables.append(table)
            
            session.add_all(tables)
            session.commit()
            print(f" Created {len(tables)} sample tables")
    except Exception as e:
        print(f"Warning: Could not create sample tables: {e}")
    finally:
        session.close()

def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()