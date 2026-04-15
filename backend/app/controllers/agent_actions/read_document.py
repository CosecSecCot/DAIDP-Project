from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from app.config.database import SessionLocal
from app.controllers.medical_controller import (
    get_patient_appointment_document_by_id,
)


# =========================
# Models
# =========================

class ReadDocumentInput(BaseModel):
    patient_id: int
    document_id: int


class ReadDocumentOutput(BaseModel):
    summary: str
    text: str
    truncated: bool


# =========================
# Helpers
# =========================

MAX_CHARS = 5000


def extract_pdf_text(file_path: Path) -> str:
    doc = fitz.open(file_path)
    text = ""

    for page in doc:
        text += page.get_text()

    return text


def extract_image_text(file_path: Path) -> str:
    return pytesseract.image_to_string(Image.open(file_path))


# =========================
# Executor
# =========================

def execute_read_document(input_data: ReadDocumentInput) -> ReadDocumentOutput:
    db = SessionLocal()

    try:
        document = get_patient_appointment_document_by_id(
            input_data.patient_id,
            input_data.document_id,
            db
        )

        file_path = Path(document.file_url)

        if not file_path.exists():
            return ReadDocumentOutput(
                summary="Document exists in records but file is missing on server.",
                text="",
                truncated=False
            )

        # 🔍 Decide extraction method
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            text = extract_pdf_text(file_path)
        elif suffix in [".png", ".jpg", ".jpeg"]:
            text = extract_image_text(file_path)
        else:
            text = "Unsupported document format."

        if not text.strip():
            return ReadDocumentOutput(
                summary="Could not extract readable text from the document.",
                text="",
                truncated=False
            )

        truncated = len(text) > MAX_CHARS
        text = text[:MAX_CHARS]

        return ReadDocumentOutput(
            summary="Document text extracted successfully.",
            text=text,
            truncated=truncated
        )

    finally:
        db.close()