from pydantic import BaseModel
from enum import Enum
from typing import Optional
from datetime import date, datetime

class AppointmentType(str, Enum):
    ONLINE  = "online"
    WALK_IN = "walk_in"

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW   = "no_show"

class BookedBy(str, Enum):
    PATIENT = "patient"
    STAFF   = "staff"
    AI      = "ai"

class AppointmentFrequency(str, Enum):
    DAILY   = "daily"
    WEEKLY  = "weekly"
    MONTHLY = "monthly"

class WaitlistStatus(str, Enum):
    WAITING = "waiting"
    OFFERED = "offered"
    EXPIRED = "expired"


# ── Appointment ───────────────────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    patient_id         : int
    doctor_id          : int
    hospital_id        : int
    department_id      : int
    scheduled_at       : datetime
    duration_mins      : Optional[int]          = 30
    type               : AppointmentType
    booked_by          : BookedBy
    booked_by_staff_id : Optional[int]          = None
    notes              : Optional[str]          = None
    series_id          : Optional[int]          = None

class AppointmentUpdate(BaseModel):
    scheduled_at  : Optional[datetime]          = None
    duration_mins : Optional[int]               = None
    status        : Optional[AppointmentStatus] = None
    notes         : Optional[str]               = None

class AppointmentResponse(BaseModel):
    id                 : int
    patient_id         : int
    doctor_id          : int
    hospital_id        : int
    department_id      : int
    series_id          : Optional[int]
    scheduled_at       : datetime
    duration_mins      : int
    type               : AppointmentType
    status             : AppointmentStatus
    booked_by          : BookedBy
    booked_by_staff_id : Optional[int]
    notes              : Optional[str]

    class Config:
        from_attributes = True


# ── Recurring ─────────────────────────────────────────────────────────────────

class RecurringCreate(BaseModel):
    patient_id        : int
    doctor_id         : int
    hospital_id       : int
    department_id     : int
    frequency         : AppointmentFrequency
    start_date        : date
    end_date          : Optional[date]          = None
    total_occurrences : Optional[int]           = None
    duration_mins     : Optional[int]           = 30
    start_time        : str
    type              : AppointmentType
    notes             : Optional[str]           = None

class RecurringResponse(BaseModel):
    id                : int
    patient_id        : int
    doctor_id         : int
    hospital_id       : int
    frequency         : AppointmentFrequency
    start_date        : date
    end_date          : Optional[date]
    total_occurrences : Optional[int]

    class Config:
        from_attributes = True


# ── Waitlist ──────────────────────────────────────────────────────────────────

class WaitlistCreate(BaseModel):
    patient_id     : int
    doctor_id      : int
    hospital_id    : int
    preferred_date : Optional[date] = None
    priority       : Optional[int]  = 0

class WaitlistUpdate(BaseModel):
    status         : Optional[WaitlistStatus] = None
    preferred_date : Optional[date]           = None
    priority       : Optional[int]            = None

class WaitlistResponse(BaseModel):
    id             : int
    patient_id     : int
    doctor_id      : int
    hospital_id    : int
    preferred_date : Optional[date]
    priority       : int
    status         : WaitlistStatus

    class Config:
        from_attributes = True