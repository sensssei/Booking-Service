import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.orm import sessionmaker
import time

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://menu_user:menu_pass@postgres:5432/menu_db")

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db_and_tables():
    retries = 10
    for i in range(retries):
        try:
            SQLModel.metadata.create_all(engine)
            print("Database connected and tables created!")
            break
        except Exception as e:
            print(f"Database not ready ({i+1}/{retries}): {e}")
            time.sleep(3)
    else:
        raise Exception("Failed to connect to database after retries")

# Dependency для FastAPI
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
