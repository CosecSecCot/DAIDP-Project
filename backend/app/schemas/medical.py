from pydantic import BaseModel
from enum import Enum
from typing import Optional
from datetime import date, datetime


class DiagnosisSeverity(str, Enum):
    MILD     = "mild"
    MODERATE = "moderate"
    SEVERE   = "severe"


class LabTestStatus(str, Enum):
    ORDERED   = "ordered"
    PENDING   = "pending"
    COMPLETED = "completed"


class DocumentType(str, Enum):
    REPORT            = "report"
    SCAN              = "scan"
    DISCHARGE_SUMMARY = "discharge_summary"
    OTHER             = "other"


class UploadedBy(str, Enum):
    DOCTOR  = "doctor"
    STAFF   = "staff"
    PATIENT = "patient"


# ── Medical Record ────────────────────────────────────────────────────────────

class MedicalRecordCreate(BaseModel):
    appointment_id        : int
    patient_id            : int
    doctor_id             : int
    visit_date            : date
    presenting_complaints : Optional[str] = None
    notes                 : Optional[str] = None
    follow_up_date        : Optional[date] = None


class MedicalRecordUpdate(BaseModel):
    presenting_complaints : Optional[str]  = None
    notes                 : Optional[str]  = None
    follow_up_date        : Optional[date] = None


class MedicalRecordResponse(BaseModel):
    id                    : int
    appointment_id        : int
    patient_id            : int
    doctor_id             : int
    visit_date            : date
    presenting_complaints : Optional[str]
    notes                 : Optional[str]
    follow_up_date        : Optional[date]

    class Config:
        from_attributes = True


# ── Diagnosis ─────────────────────────────────────────────────────────────────

class DiagnosisCreate(BaseModel):
    icd_code    : Optional[str]              = None
    description : Optional[str]             = None
    severity    : Optional[DiagnosisSeverity] = None
    is_chronic  : Optional[bool]             = False


class DiagnosisUpdate(BaseModel):
    icd_code    : Optional[str]               = None
    description : Optional[str]              = None
    severity    : Optional[DiagnosisSeverity] = None
    is_chronic  : Optional[bool]              = None


class DiagnosisResponse(BaseModel):
    id          : int
    record_id   : int
    icd_code    : Optional[str]
    description : Optional[str]
    severity    : Optional[DiagnosisSeverity]
    is_chronic  : bool

    class Config:
        from_attributes = True


# ── Lab Test ──────────────────────────────────────────────────────────────────

class LabTestCreate(BaseModel):
    test_name  : str
    notes      : Optional[str] = None


class LabTestUpdate(BaseModel):
    result             : Optional[str]           = None
    result_uploaded_at : Optional[datetime]      = None
    status             : Optional[LabTestStatus] = None
    notes              : Optional[str]           = None


class LabTestResponse(BaseModel):
    id                 : int
    record_id          : int
    patient_id         : int
    test_name          : str
    ordered_at         : Optional[datetime]
    result             : Optional[str]
    result_uploaded_at : Optional[datetime]
    status             : LabTestStatus
    notes              : Optional[str]

    class Config:
        from_attributes = True


# ── Document ──────────────────────────────────────────────────────────────────

class DocumentCreate(BaseModel):
    patient_id    : int
    record_id     : Optional[int]         = None
    uploaded_by   : UploadedBy
    file_name     : str
    file_url      : str
    document_type : Optional[DocumentType] = None


class DocumentResponse(BaseModel):
    id            : int
    patient_id    : int
    record_id     : Optional[int]
    uploaded_by   : UploadedBy
    file_name     : str
    file_url      : str
    document_type : Optional[DocumentType]
    uploaded_at   : Optional[datetime]

    class Config:
        from_attributes = True