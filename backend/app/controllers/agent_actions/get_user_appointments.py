from pydantic import BaseModel
from typing import List
from datetime import datetime

from app.config.database import SessionLocal
from app.controllers.appointment_controller import get_appointments_by_patient


class AppointmentItem(BaseModel):
    appointment_id: int
    doctor_id: int
    scheduled_at: str
    status: str


class GetUserAppointmentsInput(BaseModel):
    patient_id: int


class GetUserAppointmentsOutput(BaseModel):
    summary: str
    appointments: List[AppointmentItem]


def execute_get_user_appointments(
    input_data: GetUserAppointmentsInput,
) -> GetUserAppointmentsOutput:

    db = SessionLocal()

    try:
        appointments = get_appointments_by_patient(input_data.patient_id, db)

        items: List[AppointmentItem] = []

        for appt in appointments:
            items.append(
                AppointmentItem(
                    appointment_id=appt.id,
                    doctor_id=appt.doctor_id,
                    scheduled_at=appt.scheduled_at.isoformat()
                    if isinstance(appt.scheduled_at, datetime)
                    else str(appt.scheduled_at),
                    status=appt.status.value,
                )
            )

        return GetUserAppointmentsOutput(
            summary=f"Found {len(items)} appointments for the user.",
            appointments=items,
        )

    finally:
        db.close()