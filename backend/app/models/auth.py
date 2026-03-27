from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from app.config.database import Base
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    PATIENT = "patient"
    DOCTOR  = "doctor"
    STAFF   = "staff"
    ADMIN   = "admin"

class User(Base):
    __tablename__ = "users"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    email             = Column(String(150), nullable=False, unique=True)
    hashed_password   = Column(String(255), nullable=False)
    role              = Column(SAEnum(UserRole), nullable=False)
    linked_id         = Column(Integer)
    is_active         = Column(Boolean, default=True)
    is_verified       = Column(Boolean, default=False)
    created_at        = Column(DateTime, default=datetime.utcnow)

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, nullable=False)
    token      = Column(String(512), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)