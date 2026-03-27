from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.hospital import Hospital, Department
from app.schemas.hospital import HospitalCreate, HospitalUpdate, DepartmentCreate, DepartmentUpdate


# ── Hospital ──────────────────────────────────────────────────────────────────

def create_hospital(data: HospitalCreate, db: Session, current_user):
    # Only admin can create a hospital type
    # Admin and doctor can create a clinic type
    if data.type.value == "hospital" and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can create a hospital"
        )

    if data.type.value == "clinic" and current_user.role not in ["admin", "doctor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or doctor can create a clinic"
        )

    hospital = Hospital(
        name    = data.name,
        address = data.address,
        city    = data.city,
        phone   = data.phone,
        email   = data.email,
        type    = data.type
    )
    db.add(hospital)
    db.commit()
    db.refresh(hospital)
    return hospital


def get_all_hospitals(db: Session):
    return db.query(Hospital).filter(Hospital.is_active == True).all()


def get_hospital_by_id(hospital_id: int, db: Session):
    hospital = db.query(Hospital).filter(
        Hospital.id == hospital_id,
        Hospital.is_active == True
    ).first()
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not found"
        )
    return hospital


def update_hospital(hospital_id: int, data: HospitalUpdate, db: Session, current_user):
    hospital = get_hospital_by_id(hospital_id, db)

    # If trying to change the type, apply same role restrictions
    if data.type:
        if data.type.value == "hospital" and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin can set type to hospital"
            )
        if data.type.value == "clinic" and current_user.role not in ["admin", "doctor"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin or doctor can set type to clinic"
            )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(hospital, key, value)
    db.commit()
    db.refresh(hospital)
    return hospital


def deactivate_hospital(hospital_id: int, db: Session):
    hospital = get_hospital_by_id(hospital_id, db)
    hospital.is_active = False
    db.commit()
    return {"message": f"Hospital '{hospital.name}' has been deactivated"}


# ── Departments ───────────────────────────────────────────────────────────────

def create_department(hospital_id: int, data: DepartmentCreate, db: Session):
    get_hospital_by_id(hospital_id, db)
    department = Department(
        hospital_id = hospital_id,
        name        = data.name,
        description = data.description
    )
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


def get_all_departments(hospital_id: int, db: Session):
    get_hospital_by_id(hospital_id, db)
    return db.query(Department).filter(
        Department.hospital_id == hospital_id
    ).all()


def get_department_by_id(hospital_id: int, department_id: int, db: Session):
    get_hospital_by_id(hospital_id, db)
    department = db.query(Department).filter(
        Department.id == department_id,
        Department.hospital_id == hospital_id
    ).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    return department


def update_department(hospital_id: int, department_id: int, data: DepartmentUpdate, db: Session):
    department = get_department_by_id(hospital_id, department_id, db)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(department, key, value)
    db.commit()
    db.refresh(department)
    return department


def delete_department(hospital_id: int, department_id: int, db: Session):
    department = get_department_by_id(hospital_id, department_id, db)
    db.delete(department)
    db.commit()
    return {"message": f"Department '{department.name}' has been deleted"}