from pydantic import BaseModel
from enum import Enum
from typing import Optional
from datetime import date

class AffiliationRole(str, Enum):
    RESIDENT = "resident"
    VISITING = "visiting"

class DayOfWeek(int, Enum):
    MONDAY    = 0
    TUESDAY   = 1
    WEDNESDAY = 2
    THURSDAY  = 3
    FRIDAY    = 4
    SATURDAY  = 5
    SUNDAY    = 6

# ── Doctor ────────────────────────────────────────────────────────────────────

class DoctorCreate(BaseModel):
    full_name           : str
    email               : Optional[str] = None
    phone               : Optional[str] = None
    specialisation      : Optional[str] = None
    qualification       : Optional[str] = None
    years_of_experience : Optional[int] = None
    consultation_fee    : Optional[float] = None

class DoctorUpdate(BaseModel):
    full_name           : Optional[str] = None
    email               : Optional[str] = None
    phone               : Optional[str] = None
    specialisation      : Optional[str] = None
    qualification       : Optional[str] = None
    years_of_experience : Optional[int] = None
    consultation_fee    : Optional[float] = None

class DoctorResponse(BaseModel):
    id                  : int
    full_name           : str
    email               : Optional[str]
    phone               : Optional[str]
    specialisation      : Optional[str]
    qualification       : Optional[str]
    years_of_experience : Optional[int]
    consultation_fee    : Optional[float]
    is_active           : bool

    class Config:
        from_attributes = True

# ── Affiliation ───────────────────────────────────────────────────────────────

class AffiliationCreate(BaseModel):
    hospital_id   : int
    department_id : int
    role          : AffiliationRole
    joined_date   : Optional[date] = None

class AffiliationUpdate(BaseModel):
    role        : Optional[AffiliationRole] = None
    joined_date : Optional[date] = None

class AffiliationResponse(BaseModel):
    id            : int
    doctor_id     : int
    hospital_id   : int
    department_id : int
    role          : AffiliationRole
    joined_date   : Optional[date]

    class Config:
        from_attributes = True

# ── Availability ──────────────────────────────────────────────────────────────

class AvailabilityCreate(BaseModel):
    hospital_id        : int
    day_of_week        : DayOfWeek
    start_time         : str
    end_time           : str
    slot_duration_mins : Optional[int] = 30

class AvailabilityUpdate(BaseModel):
    day_of_week        : Optional[DayOfWeek] = None
    start_time         : Optional[str] = None
    end_time           : Optional[str] = None
    slot_duration_mins : Optional[int] = None
    is_active          : Optional[bool] = None

class AvailabilityResponse(BaseModel):
    id                 : int
    doctor_id          : int
    hospital_id        : int
    day_of_week        : int
    start_time         : str
    end_time           : str
    slot_duration_mins : int
    is_active          : bool

    class Config:
        from_attributes = True