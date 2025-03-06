from fastapi import FastAPI
from app.routers import log_router
from app.models.database import engine, Base

Base.metadata.create_all(bind=engine)
app = FastAPI()


app.include_router(log_router.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the SAP Log Parser API"}
