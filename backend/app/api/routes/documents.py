from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.db.models import Document
from app.services.documents import extract_document

router = APIRouter(prefix="/documents", tags=["documents"])
ALLOWED_TYPES = {"application/pdf", "text/plain"}


@router.post("", status_code=202)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Upload a PDF or plain text document")
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File exceeds the upload size limit")
    document_id = uuid4().hex
    root = Path(settings.upload_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    suffix = ".pdf" if file.content_type == "application/pdf" else ".txt"
    stored = root / f"{document_id}{suffix}"
    stored.write_bytes(content)
    document = Document(
        id=document_id,
        filename=Path(file.filename or "upload").name[:255],
        mime_type=file.content_type,
        storage_path=str(stored),
        processing_status="queued",
    )
    db.add(document)
    await db.commit()
    background_tasks.add_task(extract_document, document_id)
    return {"id": document_id, "filename": document.filename, "processing_status": document.processing_status}


@router.get("")
async def list_documents(db: AsyncSession = Depends(get_db)):
    documents = (await db.scalars(
        select(Document)
        .order_by(Document.created_at.desc())
    )).all()
    return [{"id": d.id, "filename": d.filename, "processing_status": d.processing_status, "created_at": d.created_at} for d in documents]
