from app.config.database import SessionLocal
from app.controllers.medical_controller import get_appointment_documents_by_patient
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class GetUserAppointmentDocumentsInput(BaseModel):
    patient_id: int

class DocumentItem(BaseModel):
    id: int
    appointment_id: Optional[int]
    file_name: str
    document_type: Optional[str]
    uploaded_at: Optional[datetime]


class GetUserAppointmentDocumentsOutput(BaseModel):
    summary: str
    documents: List[DocumentItem]

def execute_get_user_appointment_documents(
    input_data: GetUserAppointmentDocumentsInput,
) -> GetUserAppointmentDocumentsOutput:

    db = SessionLocal()
    try:
        documents = get_appointment_documents_by_patient(
            input_data.patient_id, db
        )

        items = [
            DocumentItem(
                id=doc.id,
                appointment_id=doc.appointment_id,
                file_name=doc.file_name,
                document_type=doc.document_type.value if doc.document_type else None,
                uploaded_at=doc.uploaded_at,
            )
            for doc in documents
        ]

        if not items:
            return GetUserAppointmentDocumentsOutput(
                summary="No appointment documents found.",
                documents=[]
            )

        return GetUserAppointmentDocumentsOutput(
            summary=f"Found {len(items)} appointment document(s).",
            documents=items
        )

    finally:
        db.close()