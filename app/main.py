from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware

from app.routers import log_router, dashboard_router
from app.models.database import engine, Base

Base.metadata.create_all(bind=engine)
app = FastAPI()

origins = [
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://0.0.0.0:3001",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"]
)
app.include_router(log_router.router)
app.include_router(dashboard_router.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the SAP Log Parser API"}

