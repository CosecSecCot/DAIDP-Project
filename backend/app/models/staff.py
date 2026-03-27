from sqlalchemy import Column, Integer, String, Boolean, Enum as SAEnum, DateTime
from app.config.database import Base
from datetime import datetime
import enum

class StaffRole(str, enum.Enum):
    RECEPTIONIST = "receptionist"
    NURSE        = "nurse"
    ADMIN        = "admin"

class Staff(Base):
    __tablename__ = "staff"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    hospital_id     = Column(Integer, nullable=False)
    full_name       = Column(String(150), nullable=False)
    role            = Column(SAEnum(StaffRole), nullable=False)
    email           = Column(String(150), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone           = Column(String(30))
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)