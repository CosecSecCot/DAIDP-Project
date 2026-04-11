from pydantic import BaseModel
from enum import Enum
from typing import Optional, List
from datetime import datetime


class HospitalType(str, Enum):
    CLINIC   = "clinic"
    HOSPITAL = "hospital"


class HospitalSource(str, Enum):
    MANUAL = "manual"
    OSM    = "osm"


# ── Hospital ──────────────────────────────────────────────────────────────────

class HospitalCreate(BaseModel):
    name    : str
    address : Optional[str] = None
    city    : Optional[str] = None
    phone   : Optional[str] = None
    email   : Optional[str] = None
    type    : HospitalType  = HospitalType.HOSPITAL


class HospitalUpdate(BaseModel):
    name    : Optional[str]         = None
    address : Optional[str]         = None
    city    : Optional[str]         = None
    phone   : Optional[str]         = None
    email   : Optional[str]         = None
    type    : Optional[HospitalType]= None


class HospitalResponse(BaseModel):
    id         : int
    name       : str
    address    : Optional[str]
    city       : Optional[str]
    phone      : Optional[str]
    email      : Optional[str]
    type       : HospitalType
    is_active  : bool
    osm_id     : Optional[str]
    lat        : Optional[float]
    lon        : Optional[float]
    website    : Optional[str]
    source     : HospitalSource

    class Config:
        from_attributes = True


# ── Department ────────────────────────────────────────────────────────────────

class DepartmentCreate(BaseModel):
    name        : str
    description : Optional[str] = None


class DepartmentUpdate(BaseModel):
    name        : Optional[str] = None
    description : Optional[str] = None


class DepartmentResponse(BaseModel):
    id          : int
    hospital_id : int
    name        : str
    description : Optional[str]

    class Config:
        from_attributes = True


# ── Nearby ────────────────────────────────────────────────────────────────────

class NearbySearchRequest(BaseModel):
    lat      : float
    lon      : float
    radius_m : Optional[int] = 5000


class NearbyHospitalSearchResponse(BaseModel):
    id              : int
    patient_id      : int
    search_lat      : float
    search_lon      : float
    search_radius_m : int
    hospital_id     : int
    distance_m      : Optional[float]
    searched_at     : datetime
    hospital        : HospitalResponse

    class Config:
        from_attributes = True


class NearbySearchResponse(BaseModel):
    total   : int
    results : List[NearbyHospitalSearchResponse]