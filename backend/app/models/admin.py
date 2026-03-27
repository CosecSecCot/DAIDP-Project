from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.config.database import Base
from datetime import datetime

class Admin(Base):
    __tablename__ = "admins"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    full_name       = Column(String(150), nullable=False)
    email           = Column(String(150), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone           = Column(String(30))
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)