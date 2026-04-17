from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.models.doctor import Doctor, DoctorAvailability
from app.models.hospital import Hospital
from app.controllers.agent_actions.common import get_date_candidates
from app.controllers.agent_actions.find_appointment_slots import _collect_hospitals, _collect_doctors

from app.models.ai import (
    PickerUI,
    PickerData,
    PickerOption,
)


# =========================
# Models
# =========================

class GetDoctorsInput(BaseModel):
    patient_id: int
    hospital_id: Optional[int] = None
    hospital_name: Optional[str] = None
    city: Optional[str] = None
    specialisation: Optional[str] = None
    limit: int = 10


class DoctorItem(BaseModel):
    doctor_id: int
    doctor_name: str
    hospital_id: int
    hospital_name: str
    department_id: int
    specialisation: Optional[str] = None
    experience: Optional[int] = None
    score: float


class GetDoctorsOutput(BaseModel):
    summary: str
    doctors: List[DoctorItem]
    ui: Optional[PickerUI] = None


# =========================
# Scoring Logic
# =========================

def compute_doctor_score(
    doctor: Doctor,
    hospital_id: int,
    db: Session,
    specialisation_query: Optional[str]
) -> float:
    score = 0.0

    # 🎓 Experience
    if doctor.years_of_experience:
        score += min(doctor.years_of_experience / 2, 10)

    # 🧠 Specialisation match
    if specialisation_query and doctor.specialisation:
        if specialisation_query.lower() in doctor.specialisation.lower():
            score += 10

    # 🕒 Availability
    availability = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id == doctor.id,
        DoctorAvailability.hospital_id == hospital_id,
        DoctorAvailability.is_active == True
    ).first()

    if availability:
        score += 8

    return score


# =========================
# Executor
# =========================

def execute_get_doctors(input_data: GetDoctorsInput) -> GetDoctorsOutput:
    db = SessionLocal()

    try:
        hospitals = _collect_hospitals(db, input_data)

        if not hospitals:
            return GetDoctorsOutput(
                summary="No hospitals found.",
                doctors=[],
                ui=None,
            )

        scored_doctors = []

        for hospital in hospitals:
            doctor_rows = _collect_doctors(db, hospital.id, input_data.specialisation)

            for doctor, department_id in doctor_rows:
                if department_id is None:
                    continue

                score = compute_doctor_score(
                    doctor,
                    hospital.id,
                    db,
                    input_data.specialisation
                )

                scored_doctors.append((score, doctor, hospital, department_id))

        if not scored_doctors:
            return GetDoctorsOutput(
                summary="No doctors available.",
                doctors=[],
                ui=None,
            )

        # 🔥 Sort by score
        scored_doctors.sort(key=lambda x: x[0], reverse=True)

        # 🔥 Limit
        top_doctors = scored_doctors[:input_data.limit]

        best_score = top_doctors[0][0]

        doctor_items: List[DoctorItem] = []
        options: List[PickerOption] = []

        for score, doctor, hospital, department_id in top_doctors:

            # 🧠 Badge logic
            badges = []

            if score >= best_score * 0.9:
                badges.append("Recommended")

            if doctor.years_of_experience and doctor.years_of_experience > 10:
                badges.append("Experienced")

            availability = db.query(DoctorAvailability).filter(
                DoctorAvailability.doctor_id == doctor.id,
                DoctorAvailability.hospital_id == hospital.id,
                DoctorAvailability.is_active == True
            ).first()

            if availability:
                badges.append("Available")

            badge_text = f"({' • '.join(badges)}) " if badges else ""

            label = f"{badge_text}Dr. {doctor.full_name} ({doctor.specialisation or 'General'})"

            description = f"{hospital.name} • {doctor.years_of_experience or 0} yrs exp"

            doctor_items.append(
                DoctorItem(
                    doctor_id=doctor.id,
                    doctor_name=doctor.full_name,
                    hospital_id=hospital.id,
                    hospital_name=hospital.name,
                    department_id=department_id,
                    specialisation=doctor.specialisation,
                    experience=doctor.years_of_experience,
                    score=score,
                )
            )

            options.append(
                PickerOption(
                    label=label,
                    value=str(doctor.id),
                    description=description,
                    meta={
                        "doctor_id": doctor.id,
                        "hospital_id": hospital.id,
                        "department_id": department_id,
                    },
                )
            )

        picker = PickerUI(
            component="picker",
            data=PickerData(
                title="Choose a doctor",
                prompt="Select a doctor for your appointment.",
                options=options,
                allow_multiple=False,
            ),
        )

        return GetDoctorsOutput(
            summary=f"Found {len(doctor_items)} doctor(s).",
            doctors=doctor_items,
            ui=picker,
        )

    finally:
        db.close()