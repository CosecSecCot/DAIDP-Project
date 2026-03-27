from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.config.roles import admin_only, admin_doctor_staff, any_authenticated
from app.schemas.patient import (
    PatientCreate, PatientUpdate, PatientResponse,
    HealthProfileCreate, HealthProfileUpdate, HealthProfileResponse
)
from app.controllers.patient_controller import (
    create_patient, get_all_patients, get_patient_by_id,
    update_patient, deactivate_patient,
    create_health_profile, get_health_profile, update_health_profile , delete_health_profile
)

router = APIRouter(tags=["Patients"])


# ── Patients ──────────────────────────────────────────────────────────────────

# Admin, doctor, staff can register a patient
@router.post("/patients/", response_model=PatientResponse, status_code=201)
def create(
    data: PatientCreate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return create_patient(data, db)


# Admin, doctor, staff can list all patients
@router.get("/patients/", response_model=List[PatientResponse])
def get_all(
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return get_all_patients(db)


# Everyone logged in can view a patient by id
@router.get("/patients/{patient_id}", response_model=PatientResponse)
def get_one(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_patient_by_id(patient_id, db)


# Admin, doctor, staff can update patient info
@router.put("/patients/{patient_id}", response_model=PatientResponse)
def update(
    patient_id: int,
    data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return update_patient(patient_id, data, db)


# Only admin can remove a patient
@router.delete("/patients/{patient_id}")
def delete(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(admin_only)
):
    return deactivate_patient(patient_id, db)


# ── Health Profile ────────────────────────────────────────────────────────────

# Admin, doctor, staff can create a health profile
@router.post("/patients/{patient_id}/health-profile/", response_model=HealthProfileResponse, status_code=201)
def create_profile(
    patient_id: int,
    data: HealthProfileCreate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return create_health_profile(patient_id, data, db)


# Admin, doctor, staff can view a health profile
@router.get("/patients/{patient_id}/health-profile/", response_model=HealthProfileResponse)
def get_profile(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return get_health_profile(patient_id, db)


# Admin, doctor, staff can update a health profile
@router.put("/patients/{patient_id}/health-profile/", response_model=HealthProfileResponse)
def update_profile(
    patient_id: int,
    data: HealthProfileUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return update_health_profile(patient_id, data, db)

# Admin, doctor, staff can delete a health profile
@router.delete("/patients/{patient_id}/health-profile/")
def delete_profile(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return delete_health_profile(patient_id, db)