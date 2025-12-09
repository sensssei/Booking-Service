from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_db_and_tables
from routers.menu import router as menu_router

app = FastAPI(title="Menu Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(menu_router, prefix="/menu", tags=["Menu"])

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/", tags=["Root"])
def root():
    return {"message": "Menu Service works"}
