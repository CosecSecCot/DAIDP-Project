from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.config.database import engine, Base
from app.routers import auth, hospitals, doctors, staff, patients

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
app.include_router(doctors.router)
app.include_router(staff.router)
app.include_router(patients.router)

@app.get("/")
def root():
    return {"status": "Hospital API is running"}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title="Hospital Network API",
        version="1.0.0",
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi