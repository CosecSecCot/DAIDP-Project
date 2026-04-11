from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from datetime import datetime

from app.models.medical import MedicalRecord, Diagnosis, LabTest, Document
from app.models.prescription import Prescription, PrescriptionItem
from app.schemas.medical import (
    MedicalRecordCreate, MedicalRecordUpdate,
    DiagnosisCreate, DiagnosisUpdate,
    LabTestCreate, LabTestUpdate,
    DocumentCreate
)
from app.schemas.prescription import (
    PrescriptionCreate, PrescriptionUpdate,
    PrescriptionItemCreate, PrescriptionItemUpdate
)
from app.config.file_upload import save_upload_file, delete_upload_file


# ── Medical Records ───────────────────────────────────────────────────────────

def create_medical_record(data: MedicalRecordCreate, db: Session):
    existing = db.query(MedicalRecord).filter(
        MedicalRecord.appointment_id == data.appointment_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A medical record already exists for this appointment"
        )

    record = MedicalRecord(
        appointment_id        = data.appointment_id,
        patient_id            = data.patient_id,
        doctor_id             = data.doctor_id,
        visit_date            = data.visit_date,
        presenting_complaints = data.presenting_complaints,
        notes                 = data.notes,
        follow_up_date        = data.follow_up_date
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_medical_record_by_id(record_id: int, db: Session):
    record = db.query(MedicalRecord).filter(
        MedicalRecord.id == record_id
    ).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found"
        )
    return record


def get_records_by_patient(patient_id: int, db: Session):
    return db.query(MedicalRecord).filter(
        MedicalRecord.patient_id == patient_id
    ).order_by(MedicalRecord.visit_date.desc()).all()


def update_medical_record(record_id: int, data: MedicalRecordUpdate, db: Session):
    record = get_medical_record_by_id(record_id, db)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


# ── Diagnoses ─────────────────────────────────────────────────────────────────

def add_diagnosis(record_id: int, data: DiagnosisCreate, db: Session):
    get_medical_record_by_id(record_id, db)

    diagnosis = Diagnosis(
        record_id   = record_id,
        icd_code    = data.icd_code,
        description = data.description,
        severity    = data.severity,
        is_chronic  = data.is_chronic
    )
    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)
    return diagnosis


def get_diagnoses_by_record(record_id: int, db: Session):
    get_medical_record_by_id(record_id, db)
    return db.query(Diagnosis).filter(
        Diagnosis.record_id == record_id
    ).all()


def get_diagnosis_by_id(record_id: int, diagnosis_id: int, db: Session):
    diagnosis = db.query(Diagnosis).filter(
        Diagnosis.id        == diagnosis_id,
        Diagnosis.record_id == record_id
    ).first()
    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnosis not found"
        )
    return diagnosis


def update_diagnosis(record_id: int, diagnosis_id: int, data: DiagnosisUpdate, db: Session):
    diagnosis = get_diagnosis_by_id(record_id, diagnosis_id, db)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(diagnosis, key, value)
    db.commit()
    db.refresh(diagnosis)
    return diagnosis


def delete_diagnosis(record_id: int, diagnosis_id: int, db: Session):
    diagnosis = get_diagnosis_by_id(record_id, diagnosis_id, db)
    db.delete(diagnosis)
    db.commit()
    return {"message": "Diagnosis deleted"}


# ── Lab Tests ─────────────────────────────────────────────────────────────────

def order_lab_test(record_id: int, data: LabTestCreate, db: Session):
    record = get_medical_record_by_id(record_id, db)

    lab_test = LabTest(
        record_id  = record_id,
        patient_id = record.patient_id,
        test_name  = data.test_name,
        notes      = data.notes
    )
    db.add(lab_test)
    db.commit()
    db.refresh(lab_test)
    return lab_test


def get_lab_tests_by_record(record_id: int, db: Session):
    get_medical_record_by_id(record_id, db)
    return db.query(LabTest).filter(
        LabTest.record_id == record_id
    ).all()


def get_lab_test_by_id(record_id: int, lab_test_id: int, db: Session):
    lab_test = db.query(LabTest).filter(
        LabTest.id        == lab_test_id,
        LabTest.record_id == record_id
    ).first()
    if not lab_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab test not found"
        )
    return lab_test


def update_lab_test(record_id: int, lab_test_id: int, data: LabTestUpdate, db: Session):
    lab_test = get_lab_test_by_id(record_id, lab_test_id, db)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lab_test, key, value)
    db.commit()
    db.refresh(lab_test)
    return lab_test


def delete_lab_test(record_id: int, lab_test_id: int, db: Session):
    lab_test = get_lab_test_by_id(record_id, lab_test_id, db)
    db.delete(lab_test)
    db.commit()
    return {"message": "Lab test deleted"}


# ── Documents ─────────────────────────────────────────────────────────────────

def upload_document(data: DocumentCreate, db: Session):
    document = Document(
        patient_id    = data.patient_id,
        record_id     = data.record_id,
        uploaded_by   = data.uploaded_by,
        file_name     = data.file_name,
        file_url      = data.file_url,
        document_type = data.document_type
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_documents_by_patient(patient_id: int, db: Session):
    return db.query(Document).filter(
        Document.patient_id == patient_id
    ).order_by(Document.uploaded_at.desc()).all()


def get_document_by_id(document_id: int, db: Session):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document


def delete_document(document_id: int, db: Session):
    document = get_document_by_id(document_id, db)
    db.delete(document)
    db.commit()
    return {"message": "Document deleted"}


# ── Prescriptions ─────────────────────────────────────────────────────────────

def create_prescription(record_id: int, data: PrescriptionCreate, db: Session):
    record = get_medical_record_by_id(record_id, db)

    existing = db.query(Prescription).filter(
        Prescription.record_id == record_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A prescription already exists for this record"
        )

    prescription = Prescription(
        record_id  = record_id,
        patient_id = record.patient_id,
        doctor_id  = record.doctor_id,
        notes      = data.notes
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    return prescription


def get_prescription_by_record(record_id: int, db: Session):
    get_medical_record_by_id(record_id, db)
    prescription = db.query(Prescription).filter(
        Prescription.record_id == record_id
    ).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found for this record"
        )
    return prescription


def get_prescription_by_id(prescription_id: int, db: Session):
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id
    ).first()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found"
        )
    return prescription


def update_prescription(record_id: int, prescription_id: int, data: PrescriptionUpdate, db: Session):
    prescription = get_prescription_by_id(prescription_id, db)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prescription, key, value)
    db.commit()
    db.refresh(prescription)
    return prescription


# ── Prescription Items ────────────────────────────────────────────────────────

def add_prescription_item(prescription_id: int, data: PrescriptionItemCreate, db: Session):
    get_prescription_by_id(prescription_id, db)

    item = PrescriptionItem(
        prescription_id = prescription_id,
        medicine_name   = data.medicine_name,
        dosage          = data.dosage,
        frequency       = data.frequency,
        duration        = data.duration,
        instructions    = data.instructions
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_prescription_items(prescription_id: int, db: Session):
    get_prescription_by_id(prescription_id, db)
    return db.query(PrescriptionItem).filter(
        PrescriptionItem.prescription_id == prescription_id
    ).all()


def get_prescription_item_by_id(prescription_id: int, item_id: int, db: Session):
    item = db.query(PrescriptionItem).filter(
        PrescriptionItem.id              == item_id,
        PrescriptionItem.prescription_id == prescription_id
    ).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription item not found"
        )
    return item


def update_prescription_item(prescription_id: int, item_id: int, data: PrescriptionItemUpdate, db: Session):
    item = get_prescription_item_by_id(prescription_id, item_id, db)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def delete_prescription_item(prescription_id: int, item_id: int, db: Session):
    item = get_prescription_item_by_id(prescription_id, item_id, db)
    db.delete(item)
    db.commit()
    return {"message": "Prescription item deleted"}


async def upload_document_file(
    patient_id: int,
    file: UploadFile,
    uploaded_by: str,
    record_id: int = None,
    document_type: str = None,
    db: Session = None
):
    """
    Upload a document file and save it to disk.
    
    Args:
        patient_id: ID of the patient
        file: The uploaded file
        uploaded_by: Who uploaded (doctor, staff, patient)
        record_id: Optional medical record ID
        document_type: Type of document (report, scan, discharge_summary, other)
        db: Database session
    
    Returns:
        Created Document object
    """
    # Save file to disk
    file_path = await save_upload_file(file, file_type="documents")
    
    # Create document record in DB
    document = Document(
        patient_id    = patient_id,
        record_id     = record_id,
        uploaded_by   = uploaded_by,
        file_name     = file.filename,
        file_url      = file_path,
        document_type = document_type
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document