from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError


from app.models.appointment import (
    Appointment, RecurringAppointmentSeries,
    Waitlist, AppointmentStatus, WaitlistStatus
)
from app.schemas.appointment import (
    AppointmentCreate, AppointmentUpdate,
    RecurringCreate, WaitlistCreate, WaitlistUpdate
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def check_doctor_conflict(
    doctor_id: int,
    scheduled_at: datetime,
    duration_mins: int,
    db: Session,
    exclude_id: int | None = None
):
    def normalize_dt(dt: datetime) -> datetime:
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    scheduled_at_normalized = normalize_dt(scheduled_at)
    end_time = scheduled_at_normalized + timedelta(minutes=duration_mins)

    query = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status != AppointmentStatus.CANCELLED
    )

    if exclude_id is not None:
        query = query.filter(Appointment.id != exclude_id)

    appointments = query.all()

    for appt in appointments:
        appt_start = normalize_dt(appt.scheduled_at)
        appt_end = appt_start + timedelta(minutes=appt.duration_mins)

        overlaps = scheduled_at_normalized < appt_end and end_time > appt_start

        if overlaps:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Doctor already has an appointment at this time"
            )


def generate_dates(frequency: str, start_date: date, end_date: date = None, total_occurrences: int = None):
    dates = []
    current = start_date

    while True:
        dates.append(current)

        if frequency == "daily":
            current = current + timedelta(days=1)
        elif frequency == "weekly":
            current = current + timedelta(weeks=1)
        elif frequency == "monthly":
            month = current.month + 1
            year  = current.year + (month // 13)
            month = month if month <= 12 else 1
            current = current.replace(year=year, month=month)

        if total_occurrences and len(dates) >= total_occurrences:
            break
        if end_date and current > end_date:
            break
        if not total_occurrences and not end_date:
            break

    return dates


# ── Appointments ──────────────────────────────────────────────────────────────

def create_appointment(data: AppointmentCreate, db: Session):
    duration = data.duration_mins or 30

    check_doctor_conflict(data.doctor_id, data.scheduled_at, duration, db)

    appointment = Appointment(
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        hospital_id=data.hospital_id,
        department_id=data.department_id,
        series_id=data.series_id,
        scheduled_at=data.scheduled_at,
        duration_mins=duration,
        type=data.type,
        booked_by=data.booked_by,
        booked_by_staff_id=data.booked_by_staff_id,
        notes=data.notes
    )

    try:
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        return appointment
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor already has an appointment at this exact time"
        )


def get_all_appointments(db: Session):
    return db.query(Appointment).order_by(Appointment.scheduled_at).all()


def get_appointment_by_id(appointment_id: int, db: Session):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    return appointment


def get_appointments_by_doctor(doctor_id: int, db: Session):
    return db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id
    ).order_by(Appointment.scheduled_at).all()


def get_appointments_by_patient(patient_id: int, db: Session):
    return db.query(Appointment).filter(
        Appointment.patient_id == patient_id
    ).order_by(Appointment.scheduled_at).all()


def update_appointment(appointment_id: int, data: AppointmentUpdate, db: Session):
    appointment = get_appointment_by_id(appointment_id, db)

    if appointment.status == AppointmentStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a cancelled appointment"
        )

    if data.scheduled_at:
        check_doctor_conflict(
            appointment.doctor_id,
            data.scheduled_at,
            data.duration_mins or appointment.duration_mins,
            db,
            exclude_id=appointment_id
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(appointment, key, value)

    db.commit()
    db.refresh(appointment)
    return appointment


def cancel_appointment(appointment_id: int, db: Session):
    appointment = get_appointment_by_id(appointment_id, db)

    if appointment.status == AppointmentStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment is already cancelled"
        )

    appointment.status = AppointmentStatus.CANCELLED
    db.commit()
    return {"message": "Appointment cancelled successfully"}


# ── Recurring ─────────────────────────────────────────────────────────────────

def create_recurring_series(data: RecurringCreate, db: Session):
    if not data.end_date and not data.total_occurrences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either end_date or total_occurrences"
        )

    series = RecurringAppointmentSeries(
        patient_id        = data.patient_id,
        doctor_id         = data.doctor_id,
        hospital_id       = data.hospital_id,
        department_id     = data.department_id,
        frequency         = data.frequency,
        start_date        = data.start_date,
        end_date          = data.end_date,
        total_occurrences = data.total_occurrences,
        duration_mins     = data.duration_mins,
        start_time        = data.start_time,
        type              = data.type,
        notes             = data.notes
    )
    db.add(series)
    db.commit()
    db.refresh(series)

    # Auto generate individual appointments from the series
    dates = generate_dates(
        data.frequency,
        data.start_date,
        data.end_date,
        data.total_occurrences
    )

    hour, minute = map(int, data.start_time.split(":"))

    for d in dates:
        scheduled_at = datetime(d.year, d.month, d.day, hour, minute)
        try:
            check_doctor_conflict(data.doctor_id, scheduled_at, data.duration_mins or 30, db)
            appointment = Appointment(
                patient_id    = data.patient_id,
                doctor_id     = data.doctor_id,
                hospital_id   = data.hospital_id,
                department_id = data.department_id,
                series_id     = series.id,
                scheduled_at  = scheduled_at,
                duration_mins = data.duration_mins,
                type          = data.type,
                booked_by     = "patient",
                notes         = data.notes
            )
            db.add(appointment)
        except HTTPException:
            # Skip dates that have conflicts
            continue

    db.commit()
    return series


def get_recurring_series(series_id: int, db: Session):
    series = db.query(RecurringAppointmentSeries).filter(
        RecurringAppointmentSeries.id == series_id
    ).first()
    if not series:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring series not found"
        )
    return series


def cancel_recurring_series(series_id: int, db: Session):
    series = get_recurring_series(series_id, db)

    # Cancel all future appointments in the series
    future_appointments = db.query(Appointment).filter(
        Appointment.series_id    == series_id,
        Appointment.status       != AppointmentStatus.CANCELLED,
        Appointment.scheduled_at >= datetime.utcnow()
    ).all()

    for appt in future_appointments:
        appt.status = AppointmentStatus.CANCELLED

    db.delete(series)
    db.commit()
    return {"message": f"Recurring series cancelled. {len(future_appointments)} future appointments cancelled."}


# ── Waitlist ──────────────────────────────────────────────────────────────────

def add_to_waitlist(data: WaitlistCreate, db: Session):
    existing = db.query(Waitlist).filter(
        Waitlist.patient_id == data.patient_id,
        Waitlist.doctor_id  == data.doctor_id,
        Waitlist.status     == WaitlistStatus.WAITING
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient is already on the waitlist for this doctor"
        )

    entry = Waitlist(
        patient_id     = data.patient_id,
        doctor_id      = data.doctor_id,
        hospital_id    = data.hospital_id,
        preferred_date = data.preferred_date,
        priority       = data.priority
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_all_waitlist(db: Session):
    return db.query(Waitlist).order_by(
        Waitlist.priority.desc(),
        Waitlist.added_at
    ).all()


def get_waitlist_entry(waitlist_id: int, db: Session):
    entry = db.query(Waitlist).filter(Waitlist.id == waitlist_id).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waitlist entry not found"
        )
    return entry


def get_waitlist_by_doctor(doctor_id: int, db: Session):
    return db.query(Waitlist).filter(
        Waitlist.doctor_id == doctor_id,
        Waitlist.status    == WaitlistStatus.WAITING
    ).order_by(
        Waitlist.priority.desc(),
        Waitlist.added_at
    ).all()


def update_waitlist_entry(waitlist_id: int, data: WaitlistUpdate, db: Session):
    entry = get_waitlist_entry(waitlist_id, db)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry


def remove_from_waitlist(waitlist_id: int, db: Session):
    entry = get_waitlist_entry(waitlist_id, db)
    db.delete(entry)
    db.commit()
    return {"message": "Removed from waitlist"}