from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.openapi.utils import get_openapi 
from database import create_db_and_tables
from routers.reservations import router as reservations_router
from kafka_client import stop_producer

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(" Starting Reservation Service...")
    create_db_and_tables()
    yield
    # Shutdown
    print(" Shutting down Reservation Service...")
    await stop_producer()

app = FastAPI(
    title="Reservation Service",
    description="Service for managing restaurant reservations",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reservations_router)

# ФУНКЦИЯ ДЛЯ SWAGGER АВТОРИЗАЦИИ
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Добавляем схему безопасности Bearer
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Введите JWT токен. Получите через /auth/login в Auth Service"
        }
    }
    
    # В сервисе бронирования ВСЕ эндпоинты требуют авторизации
    for path, methods in openapi_schema["paths"].items():
        for method, details in methods.items():
            details["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/")
def root():
    return {"message": "Reservation Service is running"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "reservation_service"}