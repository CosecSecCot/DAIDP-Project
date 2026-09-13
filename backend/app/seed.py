"""Development-only doctor and appointment availability seed data."""

from datetime import UTC, datetime, time, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import AppointmentSlot, Doctor


DOCTORS = (
    ("Maya Patel", "Primary care", "MediQare Central Clinic (Demo)", "Central", "Development demo provider."),
    ("Aaron Lee", "Cardiology", "MediQare Heart Clinic (Demo)", "Northside", "Development demo provider."),
    ("Sofia Chen", "Internal medicine", "MediQare Central Clinic (Demo)", "Central", "Development demo provider."),
)


async def seed_development_data() -> None:
    if settings.app_env.casefold() != "development":
        return

    first_day = datetime.now(UTC).date() + timedelta(days=1)
    slot_times = (time(10, 0), time(13, 30), time(15, 0))
    async with SessionLocal() as db:
        async with db.begin():
            for index, details in enumerate(DOCTORS):
                name, specialty, clinic, location, bio = details
                doctor = await db.scalar(select(Doctor).where(Doctor.display_name == name))
                if doctor is None:
                    doctor = Doctor(
                        display_name=name,
                        specialty=specialty,
                        clinic_name=clinic,
                        location=location,
                        bio=bio,
                    )
                    db.add(doctor)
                    await db.flush()

                # Stable future dates make startup seeding idempotent.
                for offset, slot_time in enumerate(slot_times):
                    starts_at = datetime.combine(
                        first_day + timedelta(days=offset + index),
                        slot_time,
                        tzinfo=UTC,
                    )
                    existing = await db.scalar(
                        select(AppointmentSlot.id).where(
                            AppointmentSlot.doctor_id == doctor.id,
                            AppointmentSlot.starts_at == starts_at,
                        )
                    )
                    if existing is None:
                        db.add(AppointmentSlot(
                            doctor_id=doctor.id,
                            starts_at=starts_at,
                            duration_minutes=30,
                            visit_type="in_person",
                        ))
