from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.staff import Staff
from app.models.admin import Admin

from app.schemas.auth import (
    RegisterPatient, RegisterDoctor,
    RegisterStaff, RegisterAdmin, LoginRequest
)
from app.config.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)

load_dotenv()
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))

# ── Helpers ───────────────────────────────────────────────────────────────────

def find_user_by_email(email: str, db: Session):
    doctor  = db.query(Doctor).filter(Doctor.email == email).first()
    if doctor:
        return doctor, "doctor"

    patient = db.query(Patient).filter(Patient.email == email).first()
    if patient:
        return patient, "patient"

    staff   = db.query(Staff).filter(Staff.email == email).first()
    if staff:
        return staff, "staff"

    admin   = db.query(Admin).filter(Admin.email == email).first()
    if admin:
        return admin, "admin"

    return None, None


# ── Register ──────────────────────────────────────────────────────────────────

def register_patient(data: RegisterPatient, db: Session):
    user, _ = find_user_by_email(data.email, db)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    patient = Patient(
        full_name              = data.full_name,
        email                  = data.email,
        hashed_password        = hash_password(data.password),
        phone                  = data.phone,
        date_of_birth          = data.date_of_birth,
        gender                 = data.gender,
        address                = data.address,
        blood_group            = data.blood_group,
        registered_hospital_id = data.registered_hospital_id
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient, "patient"


def register_doctor(data: RegisterDoctor, db: Session):
    user, _ = find_user_by_email(data.email, db)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    doctor = Doctor(
        full_name           = data.full_name,
        email               = data.email,
        hashed_password     = hash_password(data.password),
        phone               = data.phone,
        specialisation      = data.specialisation,
        qualification       = data.qualification,
        years_of_experience = data.years_of_experience,
        consultation_fee    = data.consultation_fee
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor, "doctor"


def register_staff(data: RegisterStaff, db: Session):
    user, _ = find_user_by_email(data.email, db)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    staff = Staff(
        full_name       = data.full_name,
        email           = data.email,
        hashed_password = hash_password(data.password),
        phone           = data.phone,
        hospital_id     = data.hospital_id,
        role            = data.role
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff, "staff"


def register_admin(data: RegisterAdmin, db: Session):
    user, _ = find_user_by_email(data.email, db)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    admin = Admin(
        full_name       = data.full_name,
        email           = data.email,
        hashed_password = hash_password(data.password),
        phone           = data.phone
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin, "admin"


# ── Login ─────────────────────────────────────────────────────────────────────

def login_user(data: LoginRequest, db: Session):
    user, role = find_user_by_email(data.email, db)

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    access_token  = create_access_token({"sub": str(user.id), "role": role})
    refresh_token = create_refresh_token({"sub": str(user.id), "role": role})

    return access_token, refresh_token, user, role


# ── Refresh ───────────────────────────────────────────────────────────────────

def refresh_access_token(refresh_token: str, db: Session):
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    new_access_token = create_access_token({
        "sub" : payload["sub"],
        "role": payload["role"]
    })
    return new_access_token


# ── Me ────────────────────────────────────────────────────────────────────────

def get_me(user_id: int, role: str, db: Session):
    if role == "doctor":
        user = db.query(Doctor).filter(Doctor.id == user_id).first()
    elif role == "patient":
        user = db.query(Patient).filter(Patient.id == user_id).first()
    elif role == "staff":
        user = db.query(Staff).filter(Staff.id == user_id).first()
    elif role == "admin":
        user = db.query(Admin).filter(Admin.id == user_id).first()
    else:
        user = None

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user, role