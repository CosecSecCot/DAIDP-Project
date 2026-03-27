from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.security import get_current_user_dependency, oauth2_scheme, decode_token
from app.schemas.auth import (
    RegisterPatient, RegisterDoctor, RegisterStaff, RegisterAdmin,
    LoginRequest, TokenResponse, MeResponse
)
from app.controllers.auth_controller import (
    register_patient, register_doctor, register_staff, register_admin,
    login_user, refresh_access_token, get_me
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register/patient", status_code=201)
def reg_patient(data: RegisterPatient, db: Session = Depends(get_db)):
    user, role = register_patient(data, db)
    return {"message": "Patient registered successfully", "id": user.id, "role": role}


@router.post("/register/doctor", status_code=201)
def reg_doctor(data: RegisterDoctor, db: Session = Depends(get_db)):
    user, role = register_doctor(data, db)
    return {"message": "Doctor registered successfully", "id": user.id, "role": role}


@router.post("/register/staff", status_code=201)
def reg_staff(data: RegisterStaff, db: Session = Depends(get_db)):
    user, role = register_staff(data, db)
    return {"message": "Staff registered successfully", "id": user.id, "role": role}


@router.post("/register/admin", status_code=201)
def reg_admin(data: RegisterAdmin, db: Session = Depends(get_db)):
    user, role = register_admin(data, db)
    return {"message": "Admin registered successfully", "id": user.id, "role": role}


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    access_token, refresh_token, user, role = login_user(data, db)

    response.set_cookie(
        key      = "refresh_token",
        value    = refresh_token,
        httponly = True,
        secure   = False,
        samesite = "lax",
        max_age  = 7 * 24 * 60 * 60
    )

    return {
        "access_token": access_token,
        "token_type"  : "bearer",
        "role"        : role,
        "id"          : user.id
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    new_token = refresh_access_token(refresh_token, db)
    return {
        "access_token": new_token,
        "token_type"  : "bearer",
        "role"        : payload.get("role"),
        "id"          : int(payload.get("sub"))
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=MeResponse)
def me(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
        role    = payload.get("role")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token"
        )

    user, role = get_me(user_id, role, db)
    return {
        "id"       : user.id,
        "full_name": user.full_name,
        "email"    : user.email,
        "role"     : role,
        "is_active": user.is_active
    }