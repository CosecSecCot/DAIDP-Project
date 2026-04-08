from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.doctor import Doctor, DoctorHospitalAffiliation, DoctorAvailability
from app.schemas.doctor import (
    DoctorCreate, DoctorUpdate,
    AffiliationCreate, AffiliationUpdate,
    AvailabilityCreate, AvailabilityUpdate
)


# ── Doctor ────────────────────────────────────────────────────────────────────

def create_doctor(data: DoctorCreate, db: Session):
    doctor = Doctor(
        full_name           = data.full_name,
        email               = data.email,
        hashed_password="test123",
        phone               = data.phone,
        specialisation      = data.specialisation,
        qualification       = data.qualification,
        years_of_experience = data.years_of_experience,
        consultation_fee    = data.consultation_fee
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


def get_all_doctors(db: Session):
    return db.query(Doctor).filter(Doctor.is_active == True).all()


def get_doctor_by_id(doctor_id: int, db: Session):
    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id,
        Doctor.is_active == True
    ).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    return doctor


def update_doctor(doctor_id: int, data: DoctorUpdate, db: Session):
    doctor = get_doctor_by_id(doctor_id, db)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(doctor, key, value)
    db.commit()
    db.refresh(doctor)
    return doctor


def deactivate_doctor(doctor_id: int, db: Session):
    doctor = get_doctor_by_id(doctor_id, db)
    doctor.is_active = False
    db.commit()
    return {"message": f"Doctor '{doctor.full_name}' has been deactivated"}


# ── Affiliations ──────────────────────────────────────────────────────────────

def create_affiliation(doctor_id: int, data: AffiliationCreate, db: Session):
    get_doctor_by_id(doctor_id, db)

    existing = db.query(DoctorHospitalAffiliation).filter(
        DoctorHospitalAffiliation.doctor_id   == doctor_id,
        DoctorHospitalAffiliation.hospital_id == data.hospital_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor is already affiliated with this hospital"
        )

    affiliation = DoctorHospitalAffiliation(
        doctor_id     = doctor_id,
        hospital_id   = data.hospital_id,
        department_id = data.department_id,
        role          = data.role,
        joined_date   = data.joined_date
    )
    db.add(affiliation)
    db.commit()
    db.refresh(affiliation)
    return affiliation


def get_affiliations(doctor_id: int, db: Session):
    get_doctor_by_id(doctor_id, db)
    return db.query(DoctorHospitalAffiliation).filter(
        DoctorHospitalAffiliation.doctor_id == doctor_id
    ).all()


def get_affiliation_by_id(doctor_id: int, affiliation_id: int, db: Session):
    affiliation = db.query(DoctorHospitalAffiliation).filter(
        DoctorHospitalAffiliation.id        == affiliation_id,
        DoctorHospitalAffiliation.doctor_id == doctor_id
    ).first()
    if not affiliation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Affiliation not found"
        )
    return affiliation


def delete_affiliation(doctor_id: int, affiliation_id: int, db: Session):
    affiliation = get_affiliation_by_id(doctor_id, affiliation_id, db)
    db.delete(affiliation)
    db.commit()
    return {"message": "Affiliation removed"}


# ── Availability ──────────────────────────────────────────────────────────────

def create_availability(doctor_id: int, data: AvailabilityCreate, db: Session):
    get_doctor_by_id(doctor_id, db)

    existing = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id    == doctor_id,
        DoctorAvailability.hospital_id  == data.hospital_id,
        DoctorAvailability.day_of_week  == data.day_of_week
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Availability slot already exists for this day at this hospital"
        )

    availability = DoctorAvailability(
        doctor_id          = doctor_id,
        hospital_id        = data.hospital_id,
        day_of_week        = data.day_of_week,
        start_time         = data.start_time,
        end_time           = data.end_time,
        slot_duration_mins = data.slot_duration_mins
    )
    db.add(availability)
    db.commit()
    db.refresh(availability)
    return availability


def get_availability(doctor_id: int, db: Session):
    get_doctor_by_id(doctor_id, db)
    return db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.is_active == True
    ).all()


def get_availability_slot(doctor_id: int, slot_id: int, db: Session):
    slot = db.query(DoctorAvailability).filter(
        DoctorAvailability.id        == slot_id,
        DoctorAvailability.doctor_id == doctor_id
    ).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability slot not found"
        )
    return slot


def update_availability(doctor_id: int, slot_id: int, data: AvailabilityUpdate, db: Session):
    slot = get_availability_slot(doctor_id, slot_id, db)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(slot, key, value)
    db.commit()
    db.refresh(slot)
    return slot


def delete_availability(doctor_id: int, slot_id: int, db: Session):
    slot = get_availability_slot(doctor_id, slot_id, db)
    db.delete(slot)
    db.commit()
    return {"message": "Availability slot deleted"}