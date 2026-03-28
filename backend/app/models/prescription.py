from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from app.config.database import Base
from datetime import datetime


class Prescription(Base):
    __tablename__ = "prescriptions"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    record_id       = Column(Integer, nullable=False, unique=True)
    patient_id      = Column(Integer, nullable=False)
    doctor_id       = Column(Integer, nullable=False)
    issued_at       = Column(DateTime, default=datetime.utcnow)
    notes           = Column(Text)
    is_active       = Column(Boolean, default=True)


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    prescription_id = Column(Integer, nullable=False)
    medicine_name   = Column(String(150), nullable=False)
    dosage          = Column(String(50))
    frequency       = Column(String(50))
    duration        = Column(String(50))
    instructions    = Column(Text)