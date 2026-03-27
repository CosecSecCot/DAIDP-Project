from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.config.roles import admin_only, admin_or_doctor, any_authenticated
from app.models.auth import User
from app.schemas.doctor import (
    DoctorCreate, DoctorUpdate, DoctorResponse,
    AffiliationCreate, AffiliationUpdate, AffiliationResponse,
    AvailabilityCreate, AvailabilityUpdate, AvailabilityResponse
)
from app.controllers.doctor_controller import (
    create_doctor, get_all_doctors, get_doctor_by_id,
    update_doctor, deactivate_doctor,
    create_affiliation, get_affiliations, delete_affiliation,
    create_availability, get_availability, update_availability, delete_availability
)

router = APIRouter(tags=["Doctors"])


# ── Doctors ───────────────────────────────────────────────────────────────────

# Only admin can register a doctor
@router.post("/doctors/", response_model=DoctorResponse, status_code=201)
def create(
    data: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    return create_doctor(data, db)


@router.get("/doctors/", response_model=List[DoctorResponse])
def get_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(any_authenticated)
):
    return get_all_doctors(db)


@router.get("/doctors/{doctor_id}", response_model=DoctorResponse)
def get_one(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(any_authenticated)
):
    return get_doctor_by_id(doctor_id, db)


# Admin and doctor can update doctor profiles
@router.put("/doctors/{doctor_id}", response_model=DoctorResponse)
def update(
    doctor_id: int,
    data: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_doctor)
):
    return update_doctor(doctor_id, data, db)


# Only admin can deactivate a doctor
@router.delete("/doctors/{doctor_id}")
def deactivate(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    return deactivate_doctor(doctor_id, db)


# ── Affiliations ──────────────────────────────────────────────────────────────

# Admin can affiliate a doctor to a hospital
@router.post("/doctors/{doctor_id}/affiliations/", response_model=AffiliationResponse, status_code=201)
def add_affiliation(
    doctor_id: int,
    data: AffiliationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    return create_affiliation(doctor_id, data, db)


@router.get("/doctors/{doctor_id}/affiliations/", response_model=List[AffiliationResponse])
def list_affiliations(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(any_authenticated)
):
    return get_affiliations(doctor_id, db)


@router.delete("/doctors/{doctor_id}/affiliations/{affiliation_id}")
def remove_affiliation(
    doctor_id: int,
    affiliation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only)
):
    return delete_affiliation(doctor_id, affiliation_id, db)


# ── Availability ──────────────────────────────────────────────────────────────

# Admin and doctor can set availability
@router.post("/doctors/{doctor_id}/availability/", response_model=AvailabilityResponse, status_code=201)
def add_availability(
    doctor_id: int,
    data: AvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_doctor)
):
    return create_availability(doctor_id, data, db)


@router.get("/doctors/{doctor_id}/availability/", response_model=List[AvailabilityResponse])
def list_availability(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(any_authenticated)
):
    return get_availability(doctor_id, db)


@router.put("/doctors/{doctor_id}/availability/{slot_id}", response_model=AvailabilityResponse)
def update_slot(
    doctor_id: int,
    slot_id: int,
    data: AvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_doctor)
):
    return update_availability(doctor_id, slot_id, data, db)


@router.delete("/doctors/{doctor_id}/availability/{slot_id}")
def delete_slot(
    doctor_id: int,
    slot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_doctor)
):
    return delete_availability(doctor_id, slot_id, db)