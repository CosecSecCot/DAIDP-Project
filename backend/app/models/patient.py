from sqlalchemy import Column, Integer, String, Text, Date, Boolean, Enum as SAEnum, DateTime
from app.config.database import Base
from datetime import datetime
import enum

class Gender(str, enum.Enum):
    MALE   = "male"
    FEMALE = "female"
    OTHER  = "other"

class Patient(Base):
    __tablename__ = "patients"
    id                     = Column(Integer, primary_key=True, autoincrement=True)
    full_name              = Column(String(150), nullable=False)
    email                  = Column(String(150), unique=True, nullable=False)
    hashed_password        = Column(String(255), nullable=False)
    date_of_birth          = Column(Date)
    gender                 = Column(SAEnum(Gender))
    phone                  = Column(String(30))
    address                = Column(Text)
    blood_group            = Column(String(10))
    registered_hospital_id = Column(Integer, nullable=True)
    is_active              = Column(Boolean, default=True)
    created_at             = Column(DateTime, default=datetime.utcnow)


class PatientHealthProfile(Base):
    __tablename__ = "patient_health_profiles"

    id                      = Column(Integer, primary_key=True, autoincrement=True)
    patient_id              = Column(Integer, nullable=False, unique=True)
    known_allergies         = Column(Text)
    chronic_conditions      = Column(Text)
    emergency_contact_name  = Column(Text)
    emergency_contact_phone = Column(Text)