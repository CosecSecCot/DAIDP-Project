from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.patient import Patient, PatientHealthProfile
from app.schemas.patient import (
    PatientCreate, PatientUpdate,
    HealthProfileCreate, HealthProfileUpdate
)
from app.config.encryption import encrypt_value, decrypt_value


# ── Patient ───────────────────────────────────────────────────────────────────

def create_patient(data: PatientCreate, db: Session):
    patient = Patient(
        full_name              = data.full_name,
        date_of_birth          = data.date_of_birth,
        gender                 = data.gender,
        phone                  = data.phone,
        email                  = data.email,
        address                = data.address,
        blood_group            = data.blood_group,
        registered_hospital_id = data.registered_hospital_id
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def get_all_patients(db: Session):
    return db.query(Patient).all()


def get_patient_by_id(patient_id: int, db: Session):
    patient = db.query(Patient).filter(
        Patient.id == patient_id
    ).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    return patient


def update_patient(patient_id: int, data: PatientUpdate, db: Session):
    patient = get_patient_by_id(patient_id, db)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    return patient


def deactivate_patient(patient_id: int, db: Session):
    patient = get_patient_by_id(patient_id, db)
    db.delete(patient)
    db.commit()
    return {"message": f"Patient '{patient.full_name}' has been removed"}


# ── Health Profile ────────────────────────────────────────────────────────────

def get_health_profile(patient_id: int, db: Session):
    get_patient_by_id(patient_id, db)

    profile = db.query(PatientHealthProfile).filter(
        PatientHealthProfile.patient_id == patient_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health profile not found"
        )

    return {
        "id": profile.id,
        "patient_id": profile.patient_id,
        "known_allergies": decrypt_value(profile.known_allergies),
        "chronic_conditions": decrypt_value(profile.chronic_conditions),
        "emergency_contact_name": decrypt_value(profile.emergency_contact_name),
        "emergency_contact_phone": decrypt_value(profile.emergency_contact_phone),
    }


def create_health_profile(patient_id: int, data: HealthProfileCreate, db: Session):
    get_patient_by_id(patient_id, db)

    existing = db.query(PatientHealthProfile).filter(
        PatientHealthProfile.patient_id == patient_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Health profile already exists for this patient"
        )

    profile = PatientHealthProfile(
        patient_id=patient_id,
        known_allergies=encrypt_value(data.known_allergies),
        chronic_conditions=encrypt_value(data.chronic_conditions),
        emergency_contact_name=encrypt_value(data.emergency_contact_name),
        emergency_contact_phone=encrypt_value(data.emergency_contact_phone)
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_health_profile(patient_id: int, data: HealthProfileUpdate, db: Session):
    get_patient_by_id(patient_id, db)

    profile = db.query(PatientHealthProfile).filter(
        PatientHealthProfile.patient_id == patient_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health profile not found"
        )

    update_data = data.model_dump(exclude_unset=True)

    encrypted_fields = {
        "known_allergies",
        "chronic_conditions",
        "emergency_contact_name",
        "emergency_contact_phone"
    }

    for key, value in update_data.items():
        if key in encrypted_fields and value is not None:
            setattr(profile, key, encrypt_value(value))
        else:
            setattr(profile, key, value)

    db.commit()
    db.refresh(profile)

    return {
        "id": profile.id,
        "patient_id": profile.patient_id,
        "known_allergies": decrypt_value(profile.known_allergies),
        "chronic_conditions": decrypt_value(profile.chronic_conditions),
        "emergency_contact_name": decrypt_value(profile.emergency_contact_name),
        "emergency_contact_phone": decrypt_value(profile.emergency_contact_phone),
    }


def delete_health_profile(patient_id: int, db: Session):
    get_patient_by_id(patient_id, db)

    profile = db.query(PatientHealthProfile).filter(
        PatientHealthProfile.patient_id == patient_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health profile not found"
        )

    db.delete(profile)
    db.commit()

    return {"message": "Health profile deleted successfully"}