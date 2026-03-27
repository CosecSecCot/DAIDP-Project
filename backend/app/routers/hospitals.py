from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.config.roles import (
    admin_only,
    admin_or_doctor,
    admin_doctor_staff,
    any_authenticated
)
from app.schemas.hospital import (
    HospitalCreate, HospitalUpdate, HospitalResponse,
    DepartmentCreate, DepartmentUpdate, DepartmentResponse
)
from app.controllers.hospital_controller import (
    create_hospital, get_all_hospitals, get_hospital_by_id,
    update_hospital, deactivate_hospital,
    create_department, get_all_departments, get_department_by_id,
    update_department, delete_department
)

router = APIRouter(tags=["Hospitals"])


# ── Hospitals ─────────────────────────────────────────────────────────────────

# Only admin can create a hospital
@router.post("/hospitals/", response_model=HospitalResponse, status_code=201)
def create(
    data: HospitalCreate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_only)
):
    return create_hospital(data, db, current_user)


# Everyone logged in can view hospitals
@router.get("/hospitals/", response_model=List[HospitalResponse])
def get_all(
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_all_hospitals(db)


@router.get("/hospitals/{hospital_id}", response_model=HospitalResponse)
def get_one(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_hospital_by_id(hospital_id, db)


# Only admin can update a hospital
@router.put("/hospitals/{hospital_id}", response_model=HospitalResponse)
def update(
    hospital_id: int,
    data: HospitalUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_only)
):
    return update_hospital(hospital_id, data, db, current_user)


# Only admin can deactivate a hospital
@router.delete("/hospitals/{hospital_id}")
def deactivate(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(admin_only)
):
    return deactivate_hospital(hospital_id, db)


# ── Departments ───────────────────────────────────────────────────────────────

# Admin, doctor, staff can create a department
@router.post("/hospitals/{hospital_id}/departments/", response_model=DepartmentResponse, status_code=201)
def create_dept(
    hospital_id: int,
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return create_department(hospital_id, data, db)


# Everyone logged in can view departments
@router.get("/hospitals/{hospital_id}/departments/", response_model=List[DepartmentResponse])
def get_all_depts(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_all_departments(hospital_id, db)


@router.get("/hospitals/{hospital_id}/departments/{department_id}", response_model=DepartmentResponse)
def get_one_dept(
    hospital_id: int,
    department_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_department_by_id(hospital_id, department_id, db)


# Admin, doctor, staff can update a department
@router.put("/hospitals/{hospital_id}/departments/{department_id}", response_model=DepartmentResponse)
def update_dept(
    hospital_id: int,
    department_id: int,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return update_department(hospital_id, department_id, data, db)


# Admin, doctor, staff can delete a department
@router.delete("/hospitals/{hospital_id}/departments/{department_id}")
def delete_dept(
    hospital_id: int,
    department_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return delete_department(hospital_id, department_id, db)