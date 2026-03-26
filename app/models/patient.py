from sqlalchemy import Column, Integer, String, Text, Date, Enum as SAEnum
from app.config.database import Base
import enum

class Gender(str, enum.Enum):
    MALE   = "male"
    FEMALE = "female"
    OTHER  = "other"

class Patient(Base):
    __tablename__ = "patients"
    id                    = Column(Integer, primary_key=True, autoincrement=True)
    full_name             = Column(String(150), nullable=False)
    date_of_birth         = Column(Date)
    gender                = Column(SAEnum(Gender))
    phone                 = Column(String(30))
    email                 = Column(String(150))
    address               = Column(Text)
    blood_group           = Column(String(10))
    registered_hospital_id= Column(Integer, nullable=False)

class PatientHealthProfile(Base):
    __tablename__ = "patient_health_profiles"
    id                      = Column(Integer, primary_key=True, autoincrement=True)
    patient_id              = Column(Integer, nullable=False, unique=True)
    known_allergies         = Column(Text)
    chronic_conditions      = Column(Text)
    emergency_contact_name  = Column(String(150))
    emergency_contact_phone = Column(String(30))