from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import create_db_and_tables
from routers.auth import router as auth_router
from kafka_client import stop_producer

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Auth Service...")
    create_db_and_tables()
    yield
    # Shutdown
    print("🛑 Shutting down Auth Service...")
    await stop_producer()

app = FastAPI(
    title="Auth Service",
    description="Authentication and user management service",
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

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

@app.get("/", tags=["Root"])
def root():
    return {"message": "Auth Service works"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "auth_service"}