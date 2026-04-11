from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.config.roles import admin_only, admin_doctor_staff, any_authenticated
from app.schemas.medical import (
    MedicalRecordCreate, MedicalRecordUpdate, MedicalRecordResponse,
    DiagnosisCreate, DiagnosisUpdate, DiagnosisResponse,
    LabTestCreate, LabTestUpdate, LabTestResponse,
    DocumentCreate, DocumentResponse
)
from app.schemas.prescription import (
    PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse,
    PrescriptionItemCreate, PrescriptionItemUpdate, PrescriptionItemResponse
)
from app.controllers.medical_controller import (
    create_medical_record, get_medical_record_by_id,
    get_records_by_patient, update_medical_record,
    add_diagnosis, get_diagnoses_by_record,
    get_diagnosis_by_id, update_diagnosis, delete_diagnosis,
    order_lab_test, get_lab_tests_by_record,
    get_lab_test_by_id, update_lab_test, delete_lab_test,
    upload_document, get_documents_by_patient,
    get_document_by_id, delete_document,
    upload_document_file,
    create_prescription, get_prescription_by_record,
    get_prescription_by_id, update_prescription,
    add_prescription_item, get_prescription_items,
    get_prescription_item_by_id, update_prescription_item,
    delete_prescription_item
)

router = APIRouter(tags=["Medical"])


# ── Medical Records ───────────────────────────────────────────────────────────

# Only doctor and admin can create a medical record
@router.post("/medical-records/", response_model=MedicalRecordResponse, status_code=201)
def create_record(
    data: MedicalRecordCreate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return create_medical_record(data, db)


# Admin, doctor, staff can get a record by id
@router.get("/medical-records/{record_id}", response_model=MedicalRecordResponse)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return get_medical_record_by_id(record_id, db)


# All records for a patient
@router.get("/medical-records/patient/{patient_id}", response_model=List[MedicalRecordResponse])
def records_by_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_records_by_patient(patient_id, db)


# Only admin and doctor can update a record
@router.put("/medical-records/{record_id}", response_model=MedicalRecordResponse)
def update_record(
    record_id: int,
    data: MedicalRecordUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return update_medical_record(record_id, data, db)


# ── Diagnoses ─────────────────────────────────────────────────────────────────

# Only doctor and admin can add a diagnosis
@router.post("/medical-records/{record_id}/diagnoses/", response_model=DiagnosisResponse, status_code=201)
def create_diagnosis(
    record_id: int,
    data: DiagnosisCreate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return add_diagnosis(record_id, data, db)


@router.get("/medical-records/{record_id}/diagnoses/", response_model=List[DiagnosisResponse])
def list_diagnoses(
    record_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_diagnoses_by_record(record_id, db)


@router.put("/medical-records/{record_id}/diagnoses/{diagnosis_id}", response_model=DiagnosisResponse)
def edit_diagnosis(
    record_id: int,
    diagnosis_id: int,
    data: DiagnosisUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return update_diagnosis(record_id, diagnosis_id, data, db)


@router.delete("/medical-records/{record_id}/diagnoses/{diagnosis_id}")
def remove_diagnosis(
    record_id: int,
    diagnosis_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return delete_diagnosis(record_id, diagnosis_id, db)


# ── Lab Tests ─────────────────────────────────────────────────────────────────

@router.post("/medical-records/{record_id}/lab-tests/", response_model=LabTestResponse, status_code=201)
def create_lab_test(
    record_id: int,
    data: LabTestCreate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return order_lab_test(record_id, data, db)


@router.get("/medical-records/{record_id}/lab-tests/", response_model=List[LabTestResponse])
def list_lab_tests(
    record_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_lab_tests_by_record(record_id, db)


@router.put("/medical-records/{record_id}/lab-tests/{lab_test_id}", response_model=LabTestResponse)
def edit_lab_test(
    record_id: int,
    lab_test_id: int,
    data: LabTestUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return update_lab_test(record_id, lab_test_id, data, db)


@router.delete("/medical-records/{record_id}/lab-tests/{lab_test_id}")
def remove_lab_test(
    record_id: int,
    lab_test_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return delete_lab_test(record_id, lab_test_id, db)


# ── Documents ─────────────────────────────────────────────────────────────────

@router.post("/documents/", response_model=DocumentResponse, status_code=201)
def create_document(
    data: DocumentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return upload_document(data, db)


@router.post("/documents/upload/", response_model=DocumentResponse, status_code=201)
async def upload_document_endpoint(
    patient_id: int = Form(...),
    file: UploadFile = File(...),
    uploaded_by: str = Form(...),
    record_id: int = Form(None),
    document_type: str = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    """
    Upload a PDF or document file for a patient.
    
    Supported file types: PDF, JPG, PNG, GIF, DOC, DOCX
    Max file size: 50 MB
    """
    return await upload_document_file(
        patient_id=patient_id,
        file=file,
        uploaded_by=uploaded_by,
        record_id=record_id,
        document_type=document_type,
        db=db
    )


@router.get("/documents/patient/{patient_id}", response_model=List[DocumentResponse])
def docs_by_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_documents_by_patient(patient_id, db)


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_doc(
    document_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_document_by_id(document_id, db)


@router.delete("/documents/{document_id}")
def remove_doc(
    document_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return delete_document(document_id, db)


# ── Prescriptions ─────────────────────────────────────────────────────────────

# Only doctor and admin can create a prescription
@router.post("/medical-records/{record_id}/prescriptions/", response_model=PrescriptionResponse, status_code=201)
def create_presc(
    record_id: int,
    data: PrescriptionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return create_prescription(record_id, data, db)


@router.get("/medical-records/{record_id}/prescriptions/", response_model=PrescriptionResponse)
def get_presc(
    record_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_prescription_by_record(record_id, db)


@router.put("/medical-records/{record_id}/prescriptions/{prescription_id}", response_model=PrescriptionResponse)
def edit_presc(
    record_id: int,
    prescription_id: int,
    data: PrescriptionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return update_prescription(record_id, prescription_id, data, db)


# ── Prescription Items ────────────────────────────────────────────────────────

@router.post("/prescriptions/{prescription_id}/items/", response_model=PrescriptionItemResponse, status_code=201)
def add_item(
    prescription_id: int,
    data: PrescriptionItemCreate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return add_prescription_item(prescription_id, data, db)


@router.get("/prescriptions/{prescription_id}/items/", response_model=List[PrescriptionItemResponse])
def list_items(
    prescription_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_prescription_items(prescription_id, db)


@router.put("/prescriptions/{prescription_id}/items/{item_id}", response_model=PrescriptionItemResponse)
def edit_item(
    prescription_id: int,
    item_id: int,
    data: PrescriptionItemUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return update_prescription_item(prescription_id, item_id, data, db)


@router.delete("/prescriptions/{prescription_id}/items/{item_id}")
def remove_item(
    prescription_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return delete_prescription_item(prescription_id, item_id, db)