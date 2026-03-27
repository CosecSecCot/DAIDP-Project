from pydantic import BaseModel
from enum import Enum
from typing import Optional

class HospitalType(str, Enum):
    CLINIC   = "clinic"
    HOSPITAL = "hospital"

class HospitalCreate(BaseModel):
    name    : str
    address : Optional[str] = None
    city    : Optional[str] = None
    phone   : Optional[str] = None
    email   : Optional[str] = None
    type    : HospitalType  = HospitalType.HOSPITAL

class HospitalUpdate(BaseModel):
    name    : Optional[str] = None
    address : Optional[str] = None
    city    : Optional[str] = None
    phone   : Optional[str] = None
    email   : Optional[str] = None
    type    : Optional[HospitalType] = None

class HospitalResponse(BaseModel):
    id        : int
    name      : str
    address   : Optional[str]
    city      : Optional[str]
    phone     : Optional[str]
    email     : Optional[str]
    type      : HospitalType
    is_active : bool

    class Config:
        from_attributes = True

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