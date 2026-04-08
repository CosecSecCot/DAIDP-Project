"""
Production-grade booking agent (FINAL FIXED)

Features:
- Safe DB session handling
- ISO datetime support
- Conflict prevention (strong)
- Past-time prevention
- Correct enum handling (LOWERCASE DB)
"""

from datetime import datetime, timedelta
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
# VALIDATION
# ===============================

def _validate_time_format(slot_time: str) -> datetime:

    try:
        if "T" in slot_time:
            return datetime.fromisoformat(slot_time)

        hour, minute = map(int, slot_time.split(":"))

        today = datetime.now()

        return datetime(
            today.year,
            today.month,
            today.day,
            hour,
            minute
        )

    except Exception:
        raise ValueError("Invalid time format")


def _validate_not_past(scheduled_at: datetime):
    if scheduled_at < datetime.now():
        raise ValueError("Cannot book past time slot")


def _validate_doctor(db, doctor_id: int):
    doctor = db.query(Doctor).filter_by(id=doctor_id).first()

    if not doctor:
        raise ValueError("Doctor not found")

    return doctor


def _check_conflict(db, doctor_id: int, scheduled_at: datetime):

    end_time = scheduled_at + timedelta(minutes=30)

    conflict = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status != AppointmentStatus.CANCELLED.value,  # ✅ FIX
        Appointment.scheduled_at < end_time,
        (Appointment.scheduled_at + timedelta(minutes=30)) > scheduled_at
    ).first()

    if conflict:
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

    db = SessionLocal()

    try:
        # STEP 1: validation
        scheduled_at = _validate_time_format(slot_time)
        _validate_not_past(scheduled_at)
        _validate_doctor(db, doctor_id)

        # STEP 2: conflict check
        _check_conflict(db, doctor_id, scheduled_at)

        # STEP 3: create appointment
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            hospital_id=hospital_id,
            department_id=department_id,
            scheduled_at=scheduled_at,
            duration_mins=30,

            # ✅ FINAL FIX (IMPORTANT)
            type=AppointmentType.ONLINE.value,
            status=AppointmentStatus.SCHEDULED.value,
            booked_by=BookedBy.AI.value,

            notes=notes
        )

        # STEP 4: commit
        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        return {
            "status": "success",
            "appointment_id": appointment.id,
            "scheduled_at": scheduled_at.isoformat(),
            "doctor_id": doctor_id
        }

    except ValueError as ve:
        db.rollback()
        return {
            "status": "error",
            "message": str(ve)
        }

    except SQLAlchemyError as e:
        db.rollback()
        print("DB ERROR:", str(e))   # 👈 DEBUG
        return {
            "status": "error",
            "message": str(e)
        }

    except Exception as e:
        db.rollback()
        print("UNKNOWN ERROR:", str(e))
        return {
            "status": "error",
            "message": "Unexpected error occurred"
        }

    finally:
        db.close()