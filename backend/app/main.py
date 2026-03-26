from fastapi import FastAPI
from app.config.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hospital Network API",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"status": "Hospital API is running"}
