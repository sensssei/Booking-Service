from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_db_and_tables
from routers.auth import router as auth_router

app = FastAPI(title="Auth Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/", tags=["Root"])
def root():
    return {"message": "Auth Service works"}
