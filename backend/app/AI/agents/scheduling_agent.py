"""
Production-grade scheduling agent (fixed)

Features:
- Doctor grouping
- Proper datetime slots
- Load balancing
- Clean UI-ready output
- Correct date handling
"""

from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict

from app.config.database import SessionLocal
from app.models.doctor import Doctor, DoctorAvailability
from app.models.appointment import Appointment


db = SessionLocal()


# ===============================
# SPECIALITY MAPPING
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

    if "doctor_speciality" in entities:
        return entities["doctor_speciality"]

    symptoms = entities.get("symptoms", [])

    for s in symptoms:
        if s in SYMPTOM_TO_SPECIALITY:
            return SYMPTOM_TO_SPECIALITY[s]

    return "general"


# ===============================
# DOCTOR FETCH
# ===============================

def get_doctors_by_speciality(speciality: str, hospital_id: int):

    return db.query(Doctor).filter(
        Doctor.specialisation.ilike(f"%{speciality}%"),
        Doctor.is_active == True
    ).all()


# ===============================
# LOAD CALCULATION
# ===============================

def get_doctor_load(doctor_ids: List[int], date: datetime):

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
# DATE RESOLUTION
# ===============================

def resolve_date(entities: Dict) -> datetime:

    if "date" in entities:
        try:
            return datetime.strptime(entities["date"], "%Y-%m-%d")
        except:
            pass

    text = entities.get("raw_text", "").lower()

    if "tomorrow" in text:
        return datetime.now() + timedelta(days=1)

    return datetime.now()


# ===============================
# MAIN FUNCTION
# ===============================

def get_available_slots(
    patient_id: int,
    hospital_id: int,
    entities: Dict
) -> Dict:

    # STEP 1: resolve date
    date_obj = resolve_date(entities)
    weekday = date_obj.weekday()

    # STEP 2: infer speciality
    speciality = infer_speciality(entities)

    # STEP 3: get doctors
    doctors = get_doctors_by_speciality(speciality, hospital_id)

    if not doctors:
        return {"slots": [], "recommended": None}

    doctor_map = {d.id: d for d in doctors}
    doctor_ids = list(doctor_map.keys())

    # STEP 4: load balancing
    loads = get_doctor_load(doctor_ids, date_obj)

    # STEP 5: availability
    availabilities = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id.in_(doctor_ids),
        DoctorAvailability.day_of_week == weekday,
        DoctorAvailability.is_active == True
    ).all()

    doctor_slots = defaultdict(list)

    # STEP 6: generate slots
    for avail in availabilities:

        slots = generate_slots(avail, date_obj)

        for slot in slots:
            doctor_slots[avail.doctor_id].append({
                "time": slot,
                "load": loads[avail.doctor_id]
            })

    if not doctor_slots:
        return {"slots": [], "recommended": None}

    # STEP 7: FORMAT OUTPUT (IMPORTANT)
    doctors_output = []

    for doc_id, slots in doctor_slots.items():

        doctor = doctor_map[doc_id]

        # sort slots by load + time
        slots.sort(key=lambda x: (x["load"], x["time"]))

        formatted = []

        for s in slots[:5]:
            formatted.append({
                "display": s["time"].strftime("%d %b | %I:%M %p"),
                "value": s["time"].strftime("%Y-%m-%dT%H:%M:%S")
            })

        doctors_output.append({
            "doctor_id": doc_id,
            "doctor_name": doctor.full_name,
            "slots": formatted
        })

    # STEP 8: RECOMMENDED SLOT
    best_doc = min(doctor_slots.items(), key=lambda x: x[1][0]["load"])
    best_slot = best_doc[1][0]["time"]

    return {
        "doctors": doctors_output,
        "recommended": best_slot.strftime("%Y-%m-%dT%H:%M:%S"),
        "date": date_obj.strftime("%Y-%m-%d")
    }