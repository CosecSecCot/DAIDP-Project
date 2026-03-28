from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Prescription ──────────────────────────────────────────────────────────────

class PrescriptionCreate(BaseModel):
    notes : Optional[str] = None


class PrescriptionUpdate(BaseModel):
    notes     : Optional[str]  = None
    is_active : Optional[bool] = None


class PrescriptionResponse(BaseModel):
    id         : int
    record_id  : int
    patient_id : int
    doctor_id  : int
    issued_at  : Optional[datetime]
    notes      : Optional[str]
    is_active  : bool

    class Config:
        from_attributes = True


# ── Prescription Item ─────────────────────────────────────────────────────────

class PrescriptionItemCreate(BaseModel):
    medicine_name : str
    dosage        : Optional[str] = None
    frequency     : Optional[str] = None
    duration      : Optional[str] = None
    instructions  : Optional[str] = None


class PrescriptionItemUpdate(BaseModel):
    medicine_name : Optional[str] = None
    dosage        : Optional[str] = None
    frequency     : Optional[str] = None
    duration      : Optional[str] = None
    instructions  : Optional[str] = None


class PrescriptionItemResponse(BaseModel):
    id              : int
    prescription_id : int
    medicine_name   : str
    dosage          : Optional[str]
    frequency       : Optional[str]
    duration        : Optional[str]
    instructions    : Optional[str]

    class Config:
        from_attributes = True