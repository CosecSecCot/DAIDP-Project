from pydantic import BaseModel, EmailStr
from enum import Enum
from typing import Optional
from datetime import date

class Gender(str, Enum):
    MALE   = "male"
    FEMALE = "female"
    OTHER  = "other"

class PatientCreate(BaseModel):
    full_name              : str
    date_of_birth          : Optional[date]  = None
    gender                 : Optional[Gender] = None
    phone                  : Optional[str]   = None
    email                  : Optional[EmailStr] = None
    address                : Optional[str]   = None
    blood_group            : Optional[str]   = None
    registered_hospital_id : Optional[int] = None

class PatientUpdate(BaseModel):
    full_name     : Optional[str]    = None
    date_of_birth : Optional[date]   = None
    gender        : Optional[Gender] = None
    phone         : Optional[str]    = None
    email         : Optional[EmailStr] = None
    address       : Optional[str]    = None
    blood_group   : Optional[str]    = None

class PatientResponse(BaseModel):
    id                     : int
    full_name              : str
    date_of_birth          : Optional[date]
    gender                 : Optional[Gender]
    phone                  : Optional[str]
    email                  : Optional[str]
    address                : Optional[str]
    blood_group            : Optional[str]
    registered_hospital_id : Optional[int] = None

    class Config:
        from_attributes = True

# ── Health Profile ────────────────────────────────────────────────────────────

class HealthProfileCreate(BaseModel):
    known_allergies         : Optional[str] = None
    chronic_conditions      : Optional[str] = None
    emergency_contact_name  : Optional[str] = None
    emergency_contact_phone : Optional[str] = None

class HealthProfileUpdate(BaseModel):
    known_allergies         : Optional[str] = None
    chronic_conditions      : Optional[str] = None
    emergency_contact_name  : Optional[str] = None
    emergency_contact_phone : Optional[str] = None

class HealthProfileResponse(BaseModel):
    id                      : int
    patient_id              : int
    known_allergies         : Optional[str]
    chronic_conditions      : Optional[str]
    emergency_contact_name  : Optional[str]
    emergency_contact_phone : Optional[str]

    class Config:
        from_attributes = True