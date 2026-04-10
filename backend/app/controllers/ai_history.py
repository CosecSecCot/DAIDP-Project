from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config.database import SessionLocal
from app.models.ai_chat import AIChatMessage, AIChatSession, ChatMessageStatus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _default_title(initial_message: Optional[Any] = None) -> str:
    if isinstance(initial_message, str):
        text = initial_message.strip()
    elif isinstance(initial_message, dict):
        text = str(initial_message.get("message", "")).strip()
    else:
        text = ""

    return text[:60] if text else "New chat"


def _serialize_session(session: AIChatSession) -> Dict[str, Any]:
    return {
        "id": session.id,
        "user_id": session.user_id,
        "title": session.title,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    }


def _serialize_message(message: AIChatMessage) -> Dict[str, Any]:
    return {
        "id": message.id,
        "chat_id": message.chat_session_id,
        "user_id": message.user_id,
        "role": message.role,
        "content": message.content,
        "extra": message.extra,
        "status": message.status.value if hasattr(message.status, "value") else str(message.status),
        "timestamp": message.timestamp.isoformat() if message.timestamp else None,
        "updated_at": message.updated_at.isoformat() if message.updated_at else None,
    }


def ensure_chat_session(
    user_id: int,
    chat_id: Optional[int] = None,
    *,
    initial_message: Optional[Any] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        if chat_id is not None:
            session = db.query(AIChatSession).filter(
                AIChatSession.id == chat_id,
                AIChatSession.user_id == user_id,
            ).first()
            if session is None:
                raise ValueError("Chat session not found for user")
            return _serialize_session(session)

        session = AIChatSession(
            user_id=user_id,
            title=title or _default_title(initial_message),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return _serialize_session(session)
    finally:
        db.close()


def append_chat_message(
    user_id: int,
    chat_id: int,
    role: str,
    content: Any,
    *,
    status: str = ChatMessageStatus.COMPLETED.value,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        message = AIChatMessage(
            chat_session_id=chat_id,
            user_id=user_id,
            role=role,
            content=content,
            extra=extra,
            status=ChatMessageStatus.ACTIVE if status == ChatMessageStatus.ACTIVE.value else ChatMessageStatus.COMPLETED,
            timestamp=_utc_now(),
            updated_at=_utc_now(),
        )
        db.add(message)
        db.commit()
        db.refresh(message)

        session = db.query(AIChatSession).filter(AIChatSession.id == chat_id).first()
        if session:
            session.updated_at = _utc_now()
            db.commit()

        return _serialize_message(message)
    finally:
        db.close()


def get_persisted_history(
    user_id: int,
    chat_id: Optional[int] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        base_query = db.query(AIChatMessage).filter(
            AIChatMessage.user_id == user_id,
        )
        if chat_id is not None:
            base_query = base_query.filter(AIChatMessage.chat_session_id == chat_id)

        base_query = base_query.order_by(AIChatMessage.timestamp.asc(), AIChatMessage.id.asc())

        if limit is not None:
            rows = db.query(AIChatMessage).filter(
                AIChatMessage.user_id == user_id,
            )
            if chat_id is not None:
                rows = rows.filter(AIChatMessage.chat_session_id == chat_id)
            rows = rows.order_by(AIChatMessage.timestamp.desc(), AIChatMessage.id.desc()).limit(limit).all()
            rows = list(reversed(rows))
        else:
            rows = base_query.all()

        return [_serialize_message(message) for message in rows]
    finally:
        db.close()


def list_chat_sessions(user_id: int) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        sessions = db.query(AIChatSession).filter(
            AIChatSession.user_id == user_id
        ).order_by(AIChatSession.updated_at.desc(), AIChatSession.id.desc()).all()
        return [_serialize_session(session) for session in sessions]
    finally:
        db.close()
