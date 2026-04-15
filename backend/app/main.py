from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.config.database import engine, Base
from app.routers import (
    auth,
    hospitals,
    doctors,
    staff,
    patients,
    appointments,
    medical,
    billing,
    ai_v2,
    nearby,
)
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hospital Network API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(hospitals.router)
app.include_router(doctors.router)
app.include_router(staff.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(medical.router)
app.include_router(billing.router)
app.include_router(ai_v2.router)
app.include_router(nearby.router)


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
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    for path in schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
