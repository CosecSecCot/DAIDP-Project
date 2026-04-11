from sqlalchemy import Column, Integer, String, Boolean, Text, Enum as SAEnum, Float, DateTime
from app.config.database import Base
from datetime import datetime
import enum


class HospitalType(str, enum.Enum):
    CLINIC   = "clinic"
    HOSPITAL = "hospital"


class HospitalSource(str, enum.Enum):
    MANUAL = "manual"     # added by admin/doctor through the API
    OSM    = "osm"        # discovered via Nominatim / OpenStreetMap


class Hospital(Base):
    __tablename__ = "hospitals"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(150), nullable=False)
    address     = Column(Text)
    city        = Column(String(100))
    phone       = Column(String(30))
    email       = Column(String(150))
    type        = Column(SAEnum(HospitalType), default=HospitalType.HOSPITAL)
    is_active   = Column(Boolean, default=True)

    # ── Fields added for OSM-discovered hospitals ─────────────────────────────
    osm_id      = Column(String(50), unique=True, nullable=True)
    lat         = Column(Float, nullable=True)
    lon         = Column(Float, nullable=True)
    website     = Column(String(255), nullable=True)
    source      = Column(SAEnum(HospitalSource), default=HospitalSource.MANUAL)
    created_at  = Column(DateTime, default=datetime.utcnow)


class Department(Base):
    __tablename__ = "departments"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    hospital_id = Column(Integer, nullable=False)
    name        = Column(String(100), nullable=False)
    description = Column(Text)


class NearbyHospitalSearch(Base):
    """
    Stores each search a patient performs so we can
    show them their search history and results.
    Links to hospitals table via hospital_id.
    """
    __tablename__ = "nearby_hospital_searches"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    patient_id      = Column(Integer, nullable=False)
    search_lat      = Column(Float, nullable=False)
    search_lon      = Column(Float, nullable=False)
    search_radius_m = Column(Integer, nullable=False)
    hospital_id     = Column(Integer, nullable=False)   # FK → hospitals.id
    distance_m      = Column(Float)
    searched_at     = Column(DateTime, default=datetime.utcnow)