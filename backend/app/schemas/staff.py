from pydantic import BaseModel
from enum import Enum
from typing import Optional

class StaffRole(str, Enum):
    RECEPTIONIST = "receptionist"
    NURSE        = "nurse"
    ADMIN        = "admin"

class StaffCreate(BaseModel):
    hospital_id : int
    full_name   : str
    role        : StaffRole
    email       : Optional[str] = None
    phone       : Optional[str] = None

class StaffUpdate(BaseModel):
    full_name   : Optional[str]      = None
    role        : Optional[StaffRole]= None
    email       : Optional[str]      = None
    phone       : Optional[str]      = None
    is_active   : Optional[bool]     = None

class StaffResponse(BaseModel):
    id          : int
    hospital_id : int
    full_name   : str
    role        : StaffRole
    email       : Optional[str]
    phone       : Optional[str]
    is_active   : bool

    class Config:
        from_attributes = True