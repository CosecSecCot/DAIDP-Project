from __future__ import annotations

from types import SimpleNamespace

from app.controllers.appointment_controller import create_appointment, check_doctor_conflict
from app.controllers.agent_actions.common import get_db_session, parse_datetime, resolve_department_id
from app.models.ai import BookAppointmentInput, BookAppointmentOutput
from app.models.appointment import AppointmentType, BookedBy
from app.models.doctor import Doctor
from app.models.patient import Patient


def execute_book_appointment(input_data: BookAppointmentInput) -> BookAppointmentOutput:
    db = get_db_session()
    try:
        patient = db.query(Patient).filter(Patient.id == input_data.patient_id).first()
        if patient is None:
            return BookAppointmentOutput(summary="Patient not found.")

        doctor = db.query(Doctor).filter(Doctor.id == input_data.doctor_id, Doctor.is_active == True).first()  # noqa: E712
        if doctor is None:
            return BookAppointmentOutput(summary="Doctor not found.")

        scheduled_at = parse_datetime(input_data.scheduled_at)
        duration = input_data.duration_mins or 30

        department_id = input_data.department_id or resolve_department_id(db, input_data.doctor_id, input_data.hospital_id)
        if department_id is None:
            return BookAppointmentOutput(summary="Unable to resolve a department for this appointment.")

        check_doctor_conflict(
            doctor_id=input_data.doctor_id,
            scheduled_at=scheduled_at,
            duration_mins=duration,
            db=db,
        )

        payload = SimpleNamespace(
            patient_id=input_data.patient_id,
            doctor_id=input_data.doctor_id,
            hospital_id=input_data.hospital_id,
            department_id=department_id,
            series_id=None,
            scheduled_at=scheduled_at,
            duration_mins=duration,
            type=AppointmentType.ONLINE,
            booked_by=BookedBy.AI,
            booked_by_staff_id=None,
            notes=input_data.notes,
        )

        appointment = create_appointment(
            data=payload,
            db=db,
        )

        return BookAppointmentOutput(
            summary="Appointment booked successfully.",
            appointment_id=appointment.id,
            scheduled_at=appointment.scheduled_at,
            doctor_id=appointment.doctor_id,
            hospital_id=appointment.hospital_id,
        )
    except Exception as exc:
        return BookAppointmentOutput(summary=f"Booking failed: {exc}")
    finally:
        db.close()
