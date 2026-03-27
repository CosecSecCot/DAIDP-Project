from pydantic import BaseModel, EmailStr
from enum import Enum
from typing import Optional
from datetime import date

class UserRole(str, Enum):
    PATIENT = "patient"
    DOCTOR  = "doctor"
    STAFF   = "staff"
    ADMIN   = "admin"

class StaffRole(str, Enum):
    RECEPTIONIST = "receptionist"
    NURSE        = "nurse"
    ADMIN        = "admin"

class Gender(str, Enum):
    MALE   = "male"
    FEMALE = "female"
    OTHER  = "other"

# ── Register ──────────────────────────────────────────────────────────────────

class RegisterPatient(BaseModel):
    full_name              : str
    email                  : EmailStr
    password               : str
    phone                  : Optional[str]   = None
    date_of_birth          : Optional[date]  = None
    gender                 : Optional[Gender] = None
    address                : Optional[str]   = None
    blood_group            : Optional[str]   = None
    registered_hospital_id : int

class RegisterDoctor(BaseModel):
    full_name           : str
    email               : EmailStr
    password            : str
    phone               : Optional[str]  = None
    specialisation      : Optional[str]  = None
    qualification       : Optional[str]  = None
    years_of_experience : Optional[int]  = None
    consultation_fee    : Optional[float]= None

class RegisterStaff(BaseModel):
    full_name   : str
    email       : EmailStr
    password    : str
    phone       : Optional[str]       = None
    hospital_id : int
    role        : StaffRole

class RegisterAdmin(BaseModel):
    full_name : str
    email     : EmailStr
    password  : str
    phone     : Optional[str] = None

# ── Login ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email    : EmailStr
    password : str

# ── Responses ─────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token : str
    token_type   : str = "bearer"
    role         : str
    id           : int

class MeResponse(BaseModel):
    id        : int
    full_name : str
    email     : str
    role      : str
    is_active : bool