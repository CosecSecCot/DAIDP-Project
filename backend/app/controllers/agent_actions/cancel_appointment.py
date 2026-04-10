from __future__ import annotations

from app.config.database import SessionLocal
from app.controllers.appointment_controller import cancel_appointment as cancel_appointment_controller
from app.models.ai import CancelAppointmentInput, CancelAppointmentOutput
from app.models.appointment import Appointment


def execute_cancel_appointment(input_data: CancelAppointmentInput) -> CancelAppointmentOutput:
    db = SessionLocal()
    try:
        appointment = db.query(Appointment).filter(Appointment.id == input_data.appointment_id).first()
        if appointment is None:
            return CancelAppointmentOutput(
                summary="Appointment not found.",
                appointment_id=input_data.appointment_id,
            )

        if input_data.patient_id is not None and appointment.patient_id != input_data.patient_id:
            return CancelAppointmentOutput(
                summary="This appointment does not belong to the current patient.",
                appointment_id=input_data.appointment_id,
            )

        cancel_appointment_controller(input_data.appointment_id, db)
        return CancelAppointmentOutput(
            summary="Appointment cancelled successfully.",
            appointment_id=input_data.appointment_id,
        )
    except Exception as exc:
        return CancelAppointmentOutput(
            summary=f"Cancellation failed: {exc}",
            appointment_id=input_data.appointment_id,
        )
    finally:
        db.close()

