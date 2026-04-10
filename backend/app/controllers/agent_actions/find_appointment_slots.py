from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.models.ai import (
    LookupSlotsInput,
    LookupSlotsOutput,
    PickerData,
    PickerOption,
    PickerUI,
    SlotOption,
)
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor, DoctorAvailability, DoctorHospitalAffiliation
from app.models.hospital import Hospital, Department
from app.controllers.agent_actions.common import get_date_candidates


def _collect_hospitals(db: Session, input_data: LookupSlotsInput) -> List[Hospital]:
    query = db.query(Hospital).filter(Hospital.is_active == True)  # noqa: E712

    if input_data.hospital_id is not None:
        query = query.filter(Hospital.id == input_data.hospital_id)
    elif input_data.hospital_name:
        query = query.filter(Hospital.name.ilike(f"%{input_data.hospital_name}%"))
    elif input_data.city:
        query = query.filter(Hospital.city.ilike(f"%{input_data.city}%"))

    return query.order_by(Hospital.name.asc()).all()


def _collect_doctors(db: Session, hospital_id: int, specialisation: str | None) -> List[tuple[Doctor, int]]:
    doctor_query = db.query(Doctor, DoctorHospitalAffiliation.department_id).join(
        DoctorHospitalAffiliation,
        DoctorHospitalAffiliation.doctor_id == Doctor.id,
    ).filter(
        Doctor.is_active == True,  # noqa: E712
        DoctorHospitalAffiliation.hospital_id == hospital_id,
    )

    if specialisation:
        doctor_query = doctor_query.filter(Doctor.specialisation.ilike(f"%{specialisation}%"))

    rows = doctor_query.order_by(Doctor.full_name.asc()).all()
    return [(doctor, department_id) for doctor, department_id in rows]


def _generate_slots_for_doctor(
    db: Session,
    doctor_id: int,
    hospital_id: int,
    department_id: int,
    doctor_name: str,
    hospital_name: str,
    date_value: date,
) -> List[SlotOption]:
    weekday = date_value.weekday()
    availabilities = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.hospital_id == hospital_id,
        DoctorAvailability.day_of_week == weekday,
        DoctorAvailability.is_active == True,  # noqa: E712
    ).all()

    if not availabilities:
        return []

    booked_rows = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.hospital_id == hospital_id,
        Appointment.status != AppointmentStatus.CANCELLED,
        Appointment.scheduled_at >= datetime.combine(date_value, datetime.min.time()),
        Appointment.scheduled_at < datetime.combine(date_value + timedelta(days=1), datetime.min.time()),
    ).all()
    booked_times = {appointment.scheduled_at.replace(second=0, microsecond=0) for appointment in booked_rows}

    slots: List[SlotOption] = []
    for availability in availabilities:
        start_hour, start_minute = map(int, availability.start_time.split(":"))
        end_hour, end_minute = map(int, availability.end_time.split(":"))
        current = datetime(date_value.year, date_value.month, date_value.day, start_hour, start_minute)
        end_time = datetime(date_value.year, date_value.month, date_value.day, end_hour, end_minute)
        step = timedelta(minutes=availability.slot_duration_mins or 30)

        while current < end_time:
            normalized = current.replace(second=0, microsecond=0)
            if normalized not in booked_times:
                slots.append(
                    SlotOption(
                        label=f"{doctor_name} | {hospital_name} | {current.strftime('%d %b %Y, %I:%M %p')}",
                        value=current.isoformat(),
                        doctor_id=doctor_id,
                        doctor_name=doctor_name,
                        hospital_id=hospital_id,
                        hospital_name=hospital_name,
                        department_id=department_id,
                        scheduled_at=current,
                        description=f"Available on {current.strftime('%A')}",
                        meta={
                            "hospital_id": hospital_id,
                            "department_id": department_id,
                            "doctor_id": doctor_id,
                            "scheduled_at": current.isoformat(),
                        },
                    )
                )
            current += step
    return slots


def execute_find_appointment_slots(input_data: LookupSlotsInput) -> LookupSlotsOutput:
    db = SessionLocal()
    try:
        hospitals = _collect_hospitals(db, input_data)
        if not hospitals:
            return LookupSlotsOutput(
                summary="No active hospitals matched the search.",
                options=[],
                ui=None,
            )

        options: List[SlotOption] = []
        date_candidates = get_date_candidates(input_data.preferred_date)

        for hospital in hospitals:
            doctor_rows = _collect_doctors(db, hospital.id, input_data.specialisation)
            for doctor, department_id in doctor_rows:
                if department_id is None:
                    continue
                for candidate_date in date_candidates:
                    options.extend(
                        _generate_slots_for_doctor(
                            db=db,
                            doctor_id=doctor.id,
                            hospital_id=hospital.id,
                            department_id=department_id,
                            doctor_name=doctor.full_name,
                            hospital_name=hospital.name,
                            date_value=candidate_date,
                        )
                    )
                    if len(options) >= input_data.limit:
                        break
                if len(options) >= input_data.limit:
                    break
            if len(options) >= input_data.limit:
                break

        options = options[: input_data.limit]

        if not options:
            return LookupSlotsOutput(
                summary="No appointment slots are available right now.",
                options=[],
                ui=None,
            )

        picker = PickerUI(
            component="picker",
            data=PickerData(
                title="Choose an appointment slot",
                prompt="Select one of the available time slots.",
                options=[
                    PickerOption(
                        label=option.label,
                        value=option.value,
                        description=option.description,
                        meta=option.meta,
                    )
                    for option in options
                ],
                allow_multiple=False,
                empty_state_message=None,
            ),
        )

        return LookupSlotsOutput(
            summary=f"Found {len(options)} available appointment slot(s).",
            options=options,
            ui=picker,
        )
    finally:
        db.close()

