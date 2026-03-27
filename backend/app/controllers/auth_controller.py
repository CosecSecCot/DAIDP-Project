from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.auth import User, RefreshToken, UserRole
from app.schemas.auth import RegisterRequest, LoginRequest
from app.config.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))


def register_user(data: RegisterRequest, db: Session):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = User(
        email           = data.email,
        hashed_password = hash_password(data.password),
        role            = data.role,
        linked_id       = data.linked_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(data: LoginRequest, db: Session):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    access_token  = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id), "role": user.role})

    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete()

    db_refresh = RefreshToken(
        user_id    = user.id,
        token      = refresh_token,
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(db_refresh)
    db.commit()

    return access_token, refresh_token, user


def refresh_access_token(refresh_token: str, db: Session):
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token
    ).first()

    if not db_token or db_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token"
        )

    new_access_token = create_access_token({
        "sub" : payload["sub"],
        "role": payload["role"]
    })

    return new_access_token


def logout_user(refresh_token: str, db: Session):
    db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token
    ).delete()
    db.commit()


def get_current_user(token: str, db: Session):
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user