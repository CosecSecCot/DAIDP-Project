from sqlalchemy import Column, Integer, String, Boolean, Text, Enum as SAEnum
from app.config.database import Base
import enum

class HospitalType(str, enum.Enum):
    CLINIC   = "clinic"
    HOSPITAL = "hospital"

class Hospital(Base):
    __tablename__ = "hospitals"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(150), nullable=False)
    address    = Column(Text)
    city       = Column(String(100))
    phone      = Column(String(30))
    email      = Column(String(150))
    type       = Column(SAEnum(HospitalType), default=HospitalType.HOSPITAL)
    is_active  = Column(Boolean, default=True)

class Department(Base):
    __tablename__ = "departments"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    hospital_id = Column(Integer, nullable=False)
    name        = Column(String(100), nullable=False)
    description = Column(Text)