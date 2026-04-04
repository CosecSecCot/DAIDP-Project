# ai/agents/booking_agent.py

"""
Production-grade booking agent.

Features:
- Input validation
- Conflict prevention
- Transaction safety
- Enum-safe insertion
"""

from datetime import datetime
from typing import Dict, Any

from sqlalchemy.exc import SQLAlchemyError

from app.config.database import SessionLocal
from app.models.appointment import (
    Appointment,
    AppointmentType,
    AppointmentStatus,
    BookedBy
)
from app.models.doctor import Doctor


# ===============================
# DB SESSION
# ===============================

db = SessionLocal()


# ===============================
# VALIDATION
# ===============================

def _validate_time_format(slot_time: str) -> datetime:
    """
    Convert "HH:MM" → datetime object
    """
    try:
        hour, minute = map(int, slot_time.split(":"))

        today = datetime.now().date()

        return datetime(
            today.year,
            today.month,
            today.day,
            hour,
            minute
        )

    except Exception:
        raise ValueError("Invalid time format. Expected HH:MM")


def _validate_doctor(doctor_id: int):
    doctor = db.query(Doctor).filter_by(id=doctor_id).first()
    if not doctor:
        raise ValueError("Doctor not found")
    return doctor


def _check_conflict(doctor_id: int, scheduled_at: datetime):
    """
    Prevent double booking
    """
    existing = db.query(Appointment).filter_by(
        doctor_id=doctor_id,
        scheduled_at=scheduled_at
    ).first()

    if existing:
        raise ValueError("Slot already booked")


# ===============================
# MAIN FUNCTION
# ===============================

def book_appointment(
    patient_id: int,
    doctor_id: int,
    hospital_id: int,
    department_id: int,
    slot_time: str,
    notes: str = None
) -> Dict[str, Any]:
    """
    Book appointment safely

    Returns:
        dict with status + appointment_id
    """

    try:
        # STEP 1: validate input
        scheduled_at = _validate_time_format(slot_time)
        _validate_doctor(doctor_id)

        # STEP 2: prevent double booking
        _check_conflict(doctor_id, scheduled_at)

        # STEP 3: create appointment
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            hospital_id=hospital_id,
            department_id=department_id,
            scheduled_at=scheduled_at,
            duration_mins=30,
            type=AppointmentType.ONLINE,
            status=AppointmentStatus.SCHEDULED,
            booked_by=BookedBy.AI,
            notes=notes
        )

        # STEP 4: transaction
        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        return {
            "status": "success",
            "appointment_id": appointment.id,
            "time": slot_time,
            "doctor_id": doctor_id
        }

    except ValueError as ve:
        db.rollback()
        return {
            "status": "error",
            "message": str(ve)
        }

    except SQLAlchemyError as se:
        db.rollback()
        return {
            "status": "error",
            "message": "Database error occurred"
        }

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": "Unexpected error occurred"
        }