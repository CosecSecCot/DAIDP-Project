import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.db.models import Appointment, AppointmentSlot, Doctor
from app.api.schema import DoctorCreate, SlotCreate

router = APIRouter(tags=["appointments"])


async def require_admin(x_admin_key: str | None = Header(default=None)):
    if not settings.admin_api_key or not x_admin_key or not secrets.compare_digest(settings.admin_api_key, x_admin_key):
        raise HTTPException(status_code=403, detail="Admin key required")


@router.get("/doctors")
async def list_doctors(specialty: str | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Doctor).where(Doctor.is_active.is_(True))
    if specialty:
        query = query.where(Doctor.specialty.ilike(f"%{specialty}%"))
    doctors = (await db.scalars(query.order_by(Doctor.display_name))).all()
    return [{"id": d.id, "name": d.display_name, "specialty": d.specialty, "clinic": d.clinic_name, "location": d.location, "bio": d.bio} for d in doctors]


@router.post("/admin/doctors", dependencies=[Depends(require_admin)], status_code=201)
async def create_doctor(payload: DoctorCreate, db: AsyncSession = Depends(get_db)):
    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)
    return {"id": doctor.id, "name": doctor.display_name, "specialty": doctor.specialty}


@router.post("/admin/slots", dependencies=[Depends(require_admin)], status_code=201)
async def create_slot(payload: SlotCreate, db: AsyncSession = Depends(get_db)):
    doctor = await db.get(Doctor, payload.doctor_id)
    if doctor is None or not doctor.is_active:
        raise HTTPException(status_code=404, detail="Active doctor not found")
    slot = AppointmentSlot(**payload.model_dump())
    db.add(slot)
    await db.commit()
    await db.refresh(slot)
    return {"id": slot.id, "doctor_id": slot.doctor_id, "starts_at": slot.starts_at, "status": slot.status}


@router.get("/slots")
async def search_slots(doctor_id: int | None = None, db: AsyncSession = Depends(get_db)):
    query = select(AppointmentSlot).where(
        AppointmentSlot.status == "available",
        AppointmentSlot.starts_at >= datetime.now(UTC),
    )
    if doctor_id is not None:
        query = query.where(AppointmentSlot.doctor_id == doctor_id)
    slots = (await db.scalars(query.order_by(AppointmentSlot.starts_at).limit(100))).all()
    return [{"id": s.id, "doctor_id": s.doctor_id, "starts_at": s.starts_at, "duration_minutes": s.duration_minutes, "visit_type": s.visit_type} for s in slots]


@router.get("/appointments")
async def list_appointments(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Appointment, AppointmentSlot, Doctor).join(AppointmentSlot, Appointment.slot_id == AppointmentSlot.id).join(Doctor, Appointment.doctor_id == Doctor.id).order_by(AppointmentSlot.starts_at.desc()))).all()
    return [{"id": a.id, "doctor_id": d.id, "doctor_name": d.display_name, "slot_id": slot.id, "scheduled_at": slot.starts_at, "duration_minutes": slot.duration_minutes, "visit_type": slot.visit_type, "status": a.status} for a, slot, d in rows]
