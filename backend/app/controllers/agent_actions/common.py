from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.models.hospital import Hospital, Department
from app.models.patient import Patient, PatientHealthProfile


def get_db_session() -> Session:
    return SessionLocal()


def parse_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def normalize_patient_context(patient: Patient) -> dict:
    return {
        "patient_id": patient.id,
        "full_name": patient.full_name,
        "email": patient.email,
        "phone": patient.phone,
        "date_of_birth": patient.date_of_birth,
        "gender": patient.gender.value if getattr(patient, "gender", None) else None,
        "address": patient.address,
        "blood_group": patient.blood_group,
        "registered_hospital_id": None,
        "is_affiliated_with_hospital": False,
    }


def load_patient_and_profile(patient_id: int, db: Session) -> tuple[Optional[Patient], dict]:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return None, {}

    profile = db.query(PatientHealthProfile).filter(
        PatientHealthProfile.patient_id == patient_id
    ).first()

    health_profile = {}
    if profile:
        health_profile = {
            "known_allergies": profile.known_allergies,
            "chronic_conditions": profile.chronic_conditions,
            "emergency_contact_name": profile.emergency_contact_name,
            "emergency_contact_phone": profile.emergency_contact_phone,
        }

    return patient, health_profile


def resolve_department_id(db: Session, doctor_id: int, hospital_id: int) -> Optional[int]:
    from app.models.doctor import DoctorHospitalAffiliation

    affiliation = db.query(DoctorHospitalAffiliation).filter(
        DoctorHospitalAffiliation.doctor_id == doctor_id,
        DoctorHospitalAffiliation.hospital_id == hospital_id,
    ).first()
    if affiliation:
        return affiliation.department_id
    return None


def get_active_hospital_name(hospital: Hospital) -> str:
    return hospital.name


def get_date_candidates(preferred: Optional[date], days_ahead: int = 7) -> list[date]:
    if preferred:
        return [preferred]
    today = datetime.utcnow().date()
    return [today + timedelta(days=offset) for offset in range(days_ahead)]

