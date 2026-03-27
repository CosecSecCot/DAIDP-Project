from sqlalchemy import Column, Integer, String, Boolean, Numeric, Date, Enum as SAEnum
from app.config.database import Base
from datetime import datetime
from sqlalchemy import DateTime
import enum

class AffiliationRole(str, enum.Enum):
    RESIDENT = "resident"
    VISITING = "visiting"

class Doctor(Base):
    __tablename__ = "doctors"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    full_name           = Column(String(150), nullable=False)
    email               = Column(String(150), unique=True, nullable=False)
    hashed_password     = Column(String(255), nullable=False)
    phone               = Column(String(30))
    specialisation      = Column(String(100))
    qualification       = Column(String(100))
    years_of_experience = Column(Integer)
    consultation_fee    = Column(Numeric(10, 2))
    is_active           = Column(Boolean, default=True)
    created_at          = Column(DateTime, default=datetime.utcnow)


class DoctorHospitalAffiliation(Base):
    __tablename__ = "doctor_hospital_affiliations"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id     = Column(Integer, nullable=False)
    hospital_id   = Column(Integer, nullable=False)
    department_id = Column(Integer, nullable=False)
    role          = Column(SAEnum(AffiliationRole), nullable=False)
    joined_date   = Column(Date)


class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id          = Column(Integer, nullable=False)
    hospital_id        = Column(Integer, nullable=False)
    day_of_week        = Column(Integer, nullable=False)
    start_time         = Column(String(10), nullable=False)
    end_time           = Column(String(10), nullable=False)
    slot_duration_mins = Column(Integer, default=30)
    is_active          = Column(Boolean, default=True)