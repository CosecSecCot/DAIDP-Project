from datetime import datetime

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ConversationCreate(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    document_ids: list[str] = Field(default_factory=list)


class ConversationMessage(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    document_ids: list[str] = Field(default_factory=list)


class DoctorCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=160)
    specialty: str = Field(min_length=1, max_length=120)
    clinic_name: str = Field(min_length=1, max_length=180)
    location: str = Field(default="", max_length=240)
    bio: str = Field(default="", max_length=4000)


class SlotCreate(BaseModel):
    doctor_id: int
    starts_at: datetime
    duration_minutes: int = Field(default=30, ge=10, le=240)
    visit_type: str = Field(default="in_person", pattern="^(in_person|online)$")

    @field_validator("starts_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("starts_at must include a timezone")
        return value


class AppointmentResponse(BaseModel):
    id: int
    doctor_id: int
    slot_id: int
    status: str
    created_at: datetime
