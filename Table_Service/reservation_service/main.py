from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_db_and_tables
from routers.reservations import router as reservations_router

app = FastAPI(title="Reservation Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reservations_router, prefix="/reservations", tags=["Reservations"])

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/", tags=["Root"])
def root():
    return {"message": "Reservation Service works"}
