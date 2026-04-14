from sqlalchemy import (
    Column, Integer, String, Text,
    Date, DateTime, Enum as SAEnum, Boolean, ForeignKey
)
from app.config.database import Base
from datetime import datetime
import enum


class DiagnosisSeverity(str, enum.Enum):
    MILD     = "mild"
    MODERATE = "moderate"
    SEVERE   = "severe"


class LabTestStatus(str, enum.Enum):
    ORDERED   = "ordered"
    PENDING   = "pending"
    COMPLETED = "completed"


class DocumentType(str, enum.Enum):
    REPORT            = "report"
    SCAN              = "scan"
    DISCHARGE_SUMMARY = "discharge_summary"
    OTHER             = "other"


class UploadedBy(str, enum.Enum):
    DOCTOR  = "doctor"
    STAFF   = "staff"
    PATIENT = "patient"


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id        = Column(Integer, nullable=False, unique=True)
    patient_id            = Column(Integer, nullable=False)
    doctor_id             = Column(Integer, nullable=False)
    visit_date            = Column(Date, nullable=False)
    presenting_complaints = Column(Text)
    notes                 = Column(Text)
    follow_up_date        = Column(Date)
    created_at            = Column(DateTime, default=datetime.utcnow)


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    record_id   = Column(Integer, nullable=False)
    icd_code    = Column(String(20))
    description = Column(Text)
    severity    = Column(SAEnum(DiagnosisSeverity))
    is_chronic  = Column(Boolean, default=False)


class LabTest(Base):
    __tablename__ = "lab_tests"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    record_id          = Column(Integer, nullable=False)
    patient_id         = Column(Integer, nullable=False)
    test_name          = Column(String(150), nullable=False)
    ordered_at         = Column(DateTime, default=datetime.utcnow)
    result             = Column(Text)
    result_uploaded_at = Column(DateTime)
    status             = Column(SAEnum(LabTestStatus), default=LabTestStatus.ORDERED)
    notes              = Column(Text)


class Document(Base):
    __tablename__ = "documents"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    patient_id    = Column(Integer, nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    record_id     = Column(Integer)
    uploaded_by   = Column(SAEnum(UploadedBy), nullable=False)
    file_name     = Column(String(255), nullable=False)
    file_url      = Column(Text, nullable=False)
    document_type = Column(SAEnum(DocumentType))
    uploaded_at   = Column(DateTime, default=datetime.utcnow)
