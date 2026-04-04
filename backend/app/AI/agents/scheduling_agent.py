# ai/agents/scheduling_agent.py

"""
Production-grade scheduling agent.

Features:
- Smart doctor selection
- Slot generation
- Conflict avoidance
- Load balancing
- Recommendation engine
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from app.config.database import SessionLocal
from app.models.doctor import Doctor, DoctorAvailability
from app.models.appointment import Appointment
from app.models.hospital import Department


db = SessionLocal()


# ===============================
# SPECIALITY MAPPING (AI TRIAGE)
# ===============================

SYMPTOM_TO_SPECIALITY = {
    "fever": "general",
    "cold": "general",
    "cough": "general",
    "chest pain": "cardiology",
    "heart": "cardiology",
    "skin": "dermatology"
}


def infer_speciality(entities: Dict) -> str:
    """
    Infer doctor speciality from entities
    """
    if "doctor_speciality" in entities:
        return entities["doctor_speciality"]

    symptoms = entities.get("symptoms", [])

    for s in symptoms:
        if s in SYMPTOM_TO_SPECIALITY:
            return SYMPTOM_TO_SPECIALITY[s]

    return "general"


# ===============================
# DOCTOR SELECTION
# ===============================

def get_doctors_by_speciality(speciality: str, hospital_id: int):
    """
    Get doctors filtered by speciality
    """

    return db.query(Doctor).filter(
        Doctor.specialisation.ilike(f"%{speciality}%"),
        Doctor.is_active == True
    ).all()


# ===============================
# LOAD BALANCING (IMPORTANT)
# ===============================

def get_doctor_load(doctor_ids: List[int], date: datetime):
    """
    Count number of appointments per doctor for a day
    """

    loads = defaultdict(int)

    appointments = db.query(Appointment).filter(
        Appointment.doctor_id.in_(doctor_ids),
        Appointment.scheduled_at >= date.replace(hour=0, minute=0),
        Appointment.scheduled_at <= date.replace(hour=23, minute=59)
    ).all()

    for appt in appointments:
        loads[appt.doctor_id] += 1

    return loads


# ===============================
# SLOT GENERATION
# ===============================

def generate_slots(avail: DoctorAvailability, date_obj: datetime):
    """
    Generate time slots for one doctor
    """

    slots = []

    start_time = datetime.strptime(avail.start_time, "%H:%M").time()
    end_time = datetime.strptime(avail.end_time, "%H:%M").time()

    current = datetime.combine(date_obj.date(), start_time)
    end_dt = datetime.combine(date_obj.date(), end_time)

    while current < end_dt:

        exists = db.query(Appointment).filter_by(
            doctor_id=avail.doctor_id,
            scheduled_at=current
        ).first()

        if not exists:
            slots.append(current)

        current += timedelta(minutes=avail.slot_duration_mins)

    return slots


# ===============================
# MAIN FUNCTION
# ===============================

def get_available_slots(
    patient_id: int,
    hospital_id: int,
    entities: Dict
) -> Dict:
    """
    Main scheduling function
    """

    # Step 1: resolve date
    if "date" in entities:
        date_obj = datetime.strptime(entities["date"], "%Y-%m-%d")
    else:
        date_obj = datetime.now()

    weekday = date_obj.weekday()

    # Step 2: infer speciality
    speciality = infer_speciality(entities)

    # Step 3: fetch doctors
    doctors = get_doctors_by_speciality(speciality, hospital_id)

    if not doctors:
        return {"slots": [], "recommended": None}

    doctor_ids = [d.id for d in doctors]

    # Step 4: load balancing
    loads = get_doctor_load(doctor_ids, date_obj)

    # Step 5: fetch availability
    availabilities = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id.in_(doctor_ids),
        DoctorAvailability.day_of_week == weekday,
        DoctorAvailability.is_active == True
    ).all()

    all_slots = []

    # Step 6: generate slots
    for avail in availabilities:
        slots = generate_slots(avail, date_obj)

        for slot in slots:
            all_slots.append({
                "doctor_id": avail.doctor_id,
                "time": slot,
                "load": loads[avail.doctor_id]
            })

    if not all_slots:
        return {"slots": [], "recommended": None}

    # Step 7: sort by load (LESS load first)
    all_slots.sort(key=lambda x: (x["load"], x["time"]))

    # Step 8: format output
    formatted_slots = [
        s["time"].strftime("%H:%M") for s in all_slots[:5]
    ]

    recommended = all_slots[0]["time"].strftime("%H:%M")

    return {
        "doctor_id": all_slots[0]["doctor_id"],
        "slots": formatted_slots,
        "recommended": recommended
    }