from sqlalchemy import Column, Integer, String, Boolean, Enum as SAEnum
from app.config.database import Base
import enum

class StaffRole(str, enum.Enum):
    RECEPTIONIST = "receptionist"
    NURSE        = "nurse"
    ADMIN        = "admin"

class Staff(Base):
    __tablename__ = "staff"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    hospital_id = Column(Integer, nullable=False)
    full_name   = Column(String(150), nullable=False)
    role        = Column(SAEnum(StaffRole), nullable=False)
    email       = Column(String(150))
    phone       = Column(String(30))
    is_active   = Column(Boolean, default=True)