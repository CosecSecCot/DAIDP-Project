from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.staff import Staff
from app.schemas.staff import StaffCreate, StaffUpdate


def create_staff(data: StaffCreate, db: Session):
    staff = Staff(
        hospital_id = data.hospital_id,
        full_name   = data.full_name,
        role        = data.role,
        email       = data.email,
        phone       = data.phone
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff


def get_all_staff(db: Session):
    return db.query(Staff).filter(Staff.is_active == True).all()


def get_staff_by_id(staff_id: int, db: Session):
    staff = db.query(Staff).filter(
        Staff.id == staff_id,
        Staff.is_active == True
    ).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )
    return staff


def update_staff(staff_id: int, data: StaffUpdate, db: Session):
    staff = get_staff_by_id(staff_id, db)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(staff, key, value)
    db.commit()
    db.refresh(staff)
    return staff


def deactivate_staff(staff_id: int, db: Session):
    staff = get_staff_by_id(staff_id, db)
    staff.is_active = False
    db.commit()
    return {"message": f"Staff member '{staff.full_name}' has been deactivated"}