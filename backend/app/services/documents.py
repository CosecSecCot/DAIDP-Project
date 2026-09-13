import logging
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import Document

logger = logging.getLogger(__name__)


async def extract_document(document_id: str) -> None:
    async with SessionLocal() as db:
        document = await db.get(Document, document_id)
        if document is None:
            return
        try:
            document.processing_status = "processing"
            await db.commit()

            path = Path(document.storage_path)
            if document.mime_type == "application/pdf":
                text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
            else:
                text = path.read_text(encoding="utf-8", errors="replace")

            # PostgreSQL text columns cannot store NUL characters sometimes
            # emitted by PDF text extractors.
            document.extracted_text = text.replace("\x00", "")[:500_000]
            document.processing_status = "ready"
            await db.commit()
        except Exception:
            logger.exception("Document extraction failed for %s", document_id)
            await db.rollback()
            try:
                document = await db.get(Document, document_id)
                if document is not None:
                    document.processing_status = "failed"
                    await db.commit()
            except Exception:
                await db.rollback()
                logger.exception("Could not mark document %s as failed", document_id)


async def recover_pending_documents() -> None:
    """Retry uploads left queued or processing after an API restart."""
    async with SessionLocal() as db:
        document_ids = (await db.scalars(
            select(Document.id).where(Document.processing_status.in_(("queued", "processing")))
        )).all()

    for document_id in document_ids:
        await extract_document(document_id)
