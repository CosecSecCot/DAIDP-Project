from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    PATIENT = "patient"
    DOCTOR  = "doctor"
    STAFF   = "staff"
    ADMIN   = "admin"

class RegisterRequest(BaseModel):
    email     : EmailStr
    password  : str
    role      : UserRole
    linked_id : int | None = None

class LoginRequest(BaseModel):
    email    : EmailStr
    password : str

class TokenResponse(BaseModel):
    access_token  : str
    token_type    : str = "bearer"

class UserResponse(BaseModel):
    id          : int
    email       : str
    role        : UserRole
    is_active   : bool
    is_verified : bool

    class Config:
        from_attributes = True