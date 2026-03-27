from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.config.roles import (
    admin_only, admin_doctor_staff,
    any_authenticated
)
from app.schemas.appointment import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    RecurringCreate, RecurringResponse,
    WaitlistCreate, WaitlistUpdate, WaitlistResponse
)
from app.controllers.appointment_controller import (
    create_appointment, get_all_appointments, get_appointment_by_id,
    get_appointments_by_doctor, get_appointments_by_patient,
    update_appointment, cancel_appointment,
    create_recurring_series, get_recurring_series, cancel_recurring_series,
    add_to_waitlist, get_all_waitlist, get_waitlist_entry,
    get_waitlist_by_doctor, update_waitlist_entry, remove_from_waitlist
)

router = APIRouter(tags=["Appointments"])


# ── Appointments ──────────────────────────────────────────────────────────────

# Admin, doctor, staff and patient can book
# TODO: STOP OVERLAPPING TIME SLOTS TO BE BOOKED
@router.post("/appointments/", response_model=AppointmentResponse, status_code=201)
def create(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return create_appointment(data, db)


# Admin, doctor, staff can see all
@router.get("/appointments/", response_model=List[AppointmentResponse])
def get_all(
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return get_all_appointments(db)


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
def get_one(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_appointment_by_id(appointment_id, db)


# All appointments for a specific doctor
@router.get("/appointments/doctor/{doctor_id}", response_model=List[AppointmentResponse])
def by_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return get_appointments_by_doctor(doctor_id, db)


# All appointments for a specific patient
@router.get("/appointments/patient/{patient_id}", response_model=List[AppointmentResponse])
def by_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_appointments_by_patient(patient_id, db)


# Admin, doctor, staff can update
@router.put("/appointments/{appointment_id}", response_model=AppointmentResponse)
def update(
    appointment_id: int,
    data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return update_appointment(appointment_id, data, db)


# Everyone can cancel their own appointment
@router.delete("/appointments/{appointment_id}")
def cancel(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return cancel_appointment(appointment_id, db)


# ── Recurring ─────────────────────────────────────────────────────────────────

# Admin, doctor, staff can create recurring series
@router.post("/appointments/recurring/", response_model=RecurringResponse, status_code=201)
def create_recurring(
    data: RecurringCreate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return create_recurring_series(data, db)


@router.get("/appointments/recurring/{series_id}", response_model=RecurringResponse)
def get_recurring(
    series_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_recurring_series(series_id, db)


@router.delete("/appointments/recurring/{series_id}")
def cancel_recurring(
    series_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return cancel_recurring_series(series_id, db)


# ── Waitlist ──────────────────────────────────────────────────────────────────

# Anyone can join the waitlist
@router.post("/waitlist/", response_model=WaitlistResponse, status_code=201)
def join_waitlist(
    data: WaitlistCreate,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return add_to_waitlist(data, db)


# Admin, doctor, staff can see full waitlist
@router.get("/waitlist/", response_model=List[WaitlistResponse])
def get_waitlist(
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return get_all_waitlist(db)


@router.get("/waitlist/{waitlist_id}", response_model=WaitlistResponse)
def get_one_waitlist(
    waitlist_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_waitlist_entry(waitlist_id, db)


# Waitlist for a specific doctor
@router.get("/waitlist/doctor/{doctor_id}", response_model=List[WaitlistResponse])
def waitlist_by_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return get_waitlist_by_doctor(doctor_id, db)


# Admin, doctor, staff can update waitlist status
@router.put("/waitlist/{waitlist_id}", response_model=WaitlistResponse)
def update_waitlist(
    waitlist_id: int,
    data: WaitlistUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return update_waitlist_entry(waitlist_id, data, db)


# Anyone can remove themselves from waitlist
@router.delete("/waitlist/{waitlist_id}")
def leave_waitlist(
    waitlist_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return remove_from_waitlist(waitlist_id, db)