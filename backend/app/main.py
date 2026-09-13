from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes.conversations import router as conversations_router
from app.api.routes.documents import router as documents_router
from app.api.routes.scheduling import router as scheduling_router
from app.core import checkpoint
from app.core.config import settings
from app.db.database import Base, SessionLocal, engine
from app.db import models  # noqa: F401
from app.seed import seed_development_data
from app.services.documents import recover_pending_documents


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await seed_development_data()
    async with SessionLocal() as db:
        await db.execute(text("SELECT 1"))
    await recover_pending_documents()
    await checkpoint.initialize_graph()
    try:
        yield
    finally:
        await checkpoint.close_graph()
        await engine.dispose()


app = FastAPI(title="MediQare API", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(scheduling_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")


@app.get("/ready")
async def ready():
    async with SessionLocal() as db:
        await db.execute(text("SELECT 1"))
    return {"status": "ready"}
