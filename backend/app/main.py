from fastapi import FastAPI
from app.config.database import engine, Base
from app.routers import auth, hospitals

import app.models.hospital
import app.models.staff
import app.models.doctor
import app.models.patient
import app.models.appointment
import app.models.medical
import app.models.prescription
import app.models.billing
import app.models.auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hospital Network API",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(hospitals.router)

@app.get("/")
def root():
    return {"status": "Hospital API is running"}