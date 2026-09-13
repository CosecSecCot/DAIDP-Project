from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str] = mapped_column(String(160))
    specialty: Mapped[str] = mapped_column(String(120), index=True)
    clinic_name: Mapped[str] = mapped_column(String(180))
    location: Mapped[str] = mapped_column(String(240), default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"
    __table_args__ = (UniqueConstraint("doctor_id", "starts_at", name="uq_doctor_slot_start"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"), index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    visit_type: Mapped[str] = mapped_column(String(20), default="in_person")
    status: Mapped[str] = mapped_column(String(20), default="available", index=True)
    doctor: Mapped[Doctor] = relationship()


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    slot_id: Mapped[int] = mapped_column(ForeignKey("appointment_slots.id"), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="booked")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(120))
    storage_path: Mapped[str] = mapped_column(String(500))
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_status: Mapped[str] = mapped_column(String(20), default="queued")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
