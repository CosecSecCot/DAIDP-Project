from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.config.roles import admin_only, admin_doctor_staff, any_authenticated
from app.schemas.staff import StaffCreate, StaffUpdate, StaffResponse
from app.controllers.staff_controller import (
    create_staff, get_all_staff, get_staff_by_id,
    update_staff, deactivate_staff
)

router = APIRouter(tags=["Staff"])


# Only admin can add staff
@router.post("/staff/", response_model=StaffResponse, status_code=201)
def create(
    data: StaffCreate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_only)
):
    return create_staff(data, db)


@router.get("/staff/", response_model=List[StaffResponse])
def get_all(
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return get_all_staff(db)


@router.get("/staff/{staff_id}", response_model=StaffResponse)
def get_one(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return get_staff_by_id(staff_id, db)


# Only admin can update staff
@router.put("/staff/{staff_id}", response_model=StaffResponse)
def update(
    staff_id: int,
    data: StaffUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_only)
):
    return update_staff(staff_id, data, db)


# Only admin can deactivate staff
@router.delete("/staff/{staff_id}")
def deactivate(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(admin_only)
):
    return deactivate_staff(staff_id, db)