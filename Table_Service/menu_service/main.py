from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.openapi.utils import get_openapi  # ← ДОБАВИТЬ
from database import create_db_and_tables
from routers.menu import router as menu_router
from kafka_client import stop_producer

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(" Starting Menu Service...")
    create_db_and_tables()
    yield
    # Shutdown
    print(" Shutting down Menu Service...")
    await stop_producer()

app = FastAPI(
    title="Menu Service",
    description="Service for managing restaurant menu",
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

app.include_router(menu_router, prefix="/api/v1")

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
    
    # Добавляем security к защищенным эндпоинтам
    for path, methods in openapi_schema["paths"].items():
        for method, details in methods.items():
            # Для POST, PUT, DELETE - требуем авторизацию
            if method in ["post", "put", "delete"]:
                details["security"] = [{"BearerAuth": []}]
            # Для GET - не требуем
            else:
                # Убираем security для публичных методов
                if "security" in details:
                    del details["security"]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/", tags=["Root"])
def root():
    return {
        "service": "Menu Service",
        "status": "running",
        "endpoints": {
            "menu": "/api/v1/menu",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "menu_service"}