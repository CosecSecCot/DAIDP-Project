"""
Conversation session store for the AI front desk.

This module keeps short-term conversational memory for each user:
- current state
- booking flow data
- last AI message
- lightweight chat history
- TTL-based expiry

This is an in-memory implementation intended for development and single-server use.
Later, you can replace it with Redis or a database-backed store without changing the
public helper functions used by the orchestrator.
"""

from __future__ import annotations

import threading
import time
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.config.database import SessionLocal
from app.models.ai_chat import AIChatMessage, AIChatSession, ChatMessageStatus


class SessionStore:
    """
    Thread-safe store for active conversation sessions.

    Each session may contain:
    - state: current conversation state
    - flow: active flow name, such as "booking"
    - awaiting_slot: whether user must select a slot
    - doctor_id, hospital_id, department_id: booking context
    - entities: extracted entities from the latest AI analysis
    - history: short chat history for the active conversation
    - last_message: latest user message
    - last_ai_message: latest assistant message
    - metadata: any extra context you want to preserve
    """

    def __init__(self, default_ttl_seconds: int = 1800) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}
        self._expiry: Dict[str, float] = {}
        self._lock = threading.Lock()
        self.default_ttl_seconds = default_ttl_seconds

    def _now(self) -> float:
        return time.time()

    def _utc_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _session_key(self, user_id: int, chat_id: Optional[int] = None) -> str:
        return f"{user_id}:{chat_id or 'default'}"

    def _is_expired(self, session_key: str) -> bool:
        expiry = self._expiry.get(session_key)
        if expiry is None:
            return False
        return self._now() > expiry

    def _cleanup_if_expired(self, session_key: str) -> None:
        if self._is_expired(session_key):
            self._store.pop(session_key, None)
            self._expiry.pop(session_key, None)

    def _touch(self, session_key: str, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        self._expiry[session_key] = self._now() + ttl

    def _create_base_session(self) -> Dict[str, Any]:
        return {
            "state": "idle",
            "flow": None,
            "awaiting_slot": False,
            "doctor_id": None,
            "hospital_id": None,
            "department_id": None,
            "entities": {},
            "metadata": {},
            "history": [],
            "last_message": None,
            "last_ai_message": None,
            "created_at": self._utc_timestamp(),
            "updated_at": self._utc_timestamp(),
        }

    def _normalize_status(self, status: str) -> str:
        return (
            ChatMessageStatus.ACTIVE.value
            if status == ChatMessageStatus.ACTIVE.value
            else ChatMessageStatus.COMPLETED.value
        )

    def ensure(self, user_id: int, chat_id: Optional[int] = None, ttl_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        Ensure a session exists for the user and return a copy of it.
        """
        session_key = self._session_key(user_id, chat_id)
        with self._lock:
            self._cleanup_if_expired(session_key)
            if session_key not in self._store:
                self._store[session_key] = self._create_base_session()
                self._touch(session_key, ttl_seconds)
            return deepcopy(self._store[session_key])

    def get(self, user_id: int, chat_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Return the current session for the user.
        If no session exists or it expired, return an empty dict.
        """
        session_key = self._session_key(user_id, chat_id)
        with self._lock:
            self._cleanup_if_expired(session_key)
            if session_key not in self._store:
                return {}
            return deepcopy(self._store[session_key])

    def set(self, user_id: int, data: Dict[str, Any], chat_id: Optional[int] = None, ttl_seconds: Optional[int] = None) -> None:
        """
        Replace the whole session for a user.
        """
        session_key = self._session_key(user_id, chat_id)
        with self._lock:
            current = self._create_base_session()
            current.update(deepcopy(data))
            current["updated_at"] = self._utc_timestamp()
            if "created_at" not in current or current["created_at"] is None:
                current["created_at"] = self._utc_timestamp()

            self._store[session_key] = current
            self._touch(session_key, ttl_seconds)

    def update(self, user_id: int, updates: Dict[str, Any], chat_id: Optional[int] = None, ttl_seconds: Optional[int] = None) -> None:
        """
        Merge updates into the current session.
        If the session does not exist, it is created first.
        """
        session_key = self._session_key(user_id, chat_id)
        with self._lock:
            self._cleanup_if_expired(session_key)

            if session_key not in self._store:
                self._store[session_key] = self._create_base_session()

            for key, value in deepcopy(updates).items():
                self._store[session_key][key] = value

            self._store[session_key]["updated_at"] = self._utc_timestamp()
            self._touch(session_key, ttl_seconds)

    def set_state(self, user_id: int, state: str, chat_id: Optional[int] = None, ttl_seconds: Optional[int] = None) -> None:
        """
        Convenience helper to update only the conversation state.
        """
        self.update(user_id, {"state": state}, chat_id=chat_id, ttl_seconds=ttl_seconds)

    def get_state(self, user_id: int, chat_id: Optional[int] = None) -> str:
        """
        Return the current state for a user.
        Falls back to 'idle' if no session exists.
        """
        session = self.get(user_id, chat_id=chat_id)
        return session.get("state", "idle")

    def set_flow(self, user_id: int, flow: Optional[str], chat_id: Optional[int] = None, ttl_seconds: Optional[int] = None) -> None:
        self.update(user_id, {"flow": flow}, chat_id=chat_id, ttl_seconds=ttl_seconds)

    def append_history(
        self,
        user_id: int,
        chat_id: Optional[int],
        role: str,
        content: Any,
        ttl_seconds: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
        status: str = ChatMessageStatus.COMPLETED.value,
    ) -> None:
        """
        Append one message to the active session history.

        role should usually be 'user' or 'assistant'.
        """
        session_key = self._session_key(user_id, chat_id)
        with self._lock:
            self._cleanup_if_expired(session_key)

            if session_key not in self._store:
                self._store[session_key] = self._create_base_session()

            message = {
                "role": role,
                "content": deepcopy(content),
                "timestamp": self._utc_timestamp(),
                "status": self._normalize_status(status),
            }

            if extra:
                message["extra"] = deepcopy(extra)

            self._store[session_key].setdefault("history", [])
            self._store[session_key]["history"].append(message)
            self._store[session_key]["updated_at"] = self._utc_timestamp()
            self._touch(session_key, ttl_seconds)

    def complete_active_history(
        self,
        user_id: int,
        chat_id: Optional[int] = None,
        role: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        session_key = self._session_key(user_id, chat_id)
        with self._lock:
            self._cleanup_if_expired(session_key)

            if session_key not in self._store:
                return

            history = self._store[session_key].get("history", [])

            for entry in history:
                if entry.get("status") != ChatMessageStatus.ACTIVE.value:
                    continue
                if role and entry.get("role") != role:
                    continue
                entry["status"] = ChatMessageStatus.COMPLETED.value

            self._store[session_key]["updated_at"] = self._utc_timestamp()
            self._touch(session_key, ttl_seconds)

    def get_history(self, user_id: int, chat_id: Optional[int] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Return the conversation history for a user.
        If limit is provided, return only the most recent messages.
        """
        session = self.get(user_id, chat_id=chat_id)
        history = session.get("history", [])
        if limit is None:
            return deepcopy(history)
        return deepcopy(history[-limit:])

    def set_entities(self, user_id: int, entities: Dict[str, Any], chat_id: Optional[int] = None, ttl_seconds: Optional[int] = None) -> None:
        self.update(user_id, {"entities": deepcopy(entities)}, chat_id=chat_id, ttl_seconds=ttl_seconds)

    def get_entities(self, user_id: int, chat_id: Optional[int] = None) -> Dict[str, Any]:
        session = self.get(user_id, chat_id=chat_id)
        return deepcopy(session.get("entities", {}))

    def set_context(
        self,
        user_id: int,
        chat_id: Optional[int] = None,
        *,
        doctor_id: Optional[int] = None,
        hospital_id: Optional[int] = None,
        department_id: Optional[int] = None,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        updates: Dict[str, Any] = {}
        if doctor_id is not None:
            updates["doctor_id"] = doctor_id
        if hospital_id is not None:
            updates["hospital_id"] = hospital_id
        if department_id is not None:
            updates["department_id"] = department_id
        if updates:
            self.update(user_id, updates, chat_id=chat_id, ttl_seconds=ttl_seconds)

    def get_context(self, user_id: int, chat_id: Optional[int] = None) -> Dict[str, Any]:
        session = self.get(user_id, chat_id=chat_id)
        return {
            "doctor_id": session.get("doctor_id"),
            "hospital_id": session.get("hospital_id"),
            "department_id": session.get("department_id"),
        }

    def set_message_context(
        self,
        user_id: int,
        chat_id: Optional[int] = None,
        user_message: Optional[str] = None,
        ai_message: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        updates: Dict[str, Any] = {}
        if user_message is not None:
            updates["last_message"] = user_message
        if ai_message is not None:
            updates["last_ai_message"] = ai_message
        if updates:
            self.update(user_id, updates, chat_id=chat_id, ttl_seconds=ttl_seconds)

    def clear(self, user_id: int, chat_id: Optional[int] = None) -> None:
        """
        Remove a user's session completely.
        """
        session_key = self._session_key(user_id, chat_id)
        with self._lock:
            self._store.pop(session_key, None)
            self._expiry.pop(session_key, None)

    def exists(self, user_id: int, chat_id: Optional[int] = None) -> bool:
        session_key = self._session_key(user_id, chat_id)
        with self._lock:
            self._cleanup_if_expired(session_key)
            return session_key in self._store

    def cleanup_expired(self) -> int:
        """
        Remove all expired sessions.
        Returns how many sessions were removed.
        """
        removed = 0
        with self._lock:
            expired_ids = [user_id for user_id in self._store.keys() if self._is_expired(user_id)]
            for user_id in expired_ids:
                self._store.pop(user_id, None)
                self._expiry.pop(user_id, None)
                removed += 1
        return removed


session_store = SessionStore()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_json_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _normalize_json_value(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_normalize_json_value(item) for item in value]
    return str(value)


def _sync_embedded_status(content: Any, status: str) -> Any:
    normalized_content = deepcopy(content)

    if isinstance(normalized_content, dict):
        normalized_content["status"] = status

        ui = normalized_content.get("ui")
        if isinstance(ui, dict) and "state" in ui:
            ui["state"] = status

    return normalized_content


def _parse_status(status: str) -> ChatMessageStatus:
    return (
        ChatMessageStatus.ACTIVE
        if status == ChatMessageStatus.ACTIVE.value
        else ChatMessageStatus.COMPLETED
    )


def _serialize_chat_message(message: AIChatMessage) -> Dict[str, Any]:
    return {
        "id": message.id,
        "chat_id": message.chat_session_id,
        "user_id": message.user_id,
        "role": message.role,
        "content": deepcopy(message.content),
        "extra": deepcopy(message.extra),
        "status": message.status.value,
        "timestamp": message.timestamp.isoformat() if message.timestamp else None,
        "updated_at": message.updated_at.isoformat() if message.updated_at else None,
    }


def _serialize_chat_session(chat_session: AIChatSession) -> Dict[str, Any]:
    return {
        "id": chat_session.id,
        "user_id": chat_session.user_id,
        "title": chat_session.title,
        "created_at": chat_session.created_at.isoformat() if chat_session.created_at else None,
        "updated_at": chat_session.updated_at.isoformat() if chat_session.updated_at else None,
    }


def _default_chat_title(initial_message: Optional[Any] = None) -> str:
    if isinstance(initial_message, str):
        text = initial_message.strip()
    elif isinstance(initial_message, dict):
        text = str(initial_message.get("message", "")).strip()
    else:
        text = ""

    if not text:
        return "New chat"

    return text[:60]


def _ensure_chat_session(
    user_id: int,
    chat_id: Optional[int] = None,
    initial_message: Optional[Any] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        if chat_id is not None:
            chat_session = db.query(AIChatSession).filter(
                AIChatSession.id == chat_id,
                AIChatSession.user_id == user_id
            ).first()
            if not chat_session:
                raise ValueError("Chat session not found for user")
            return _serialize_chat_session(chat_session)

        chat_session = AIChatSession(
            user_id=user_id,
            title=title or _default_chat_title(initial_message)
        )
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
        return _serialize_chat_session(chat_session)
    finally:
        db.close()


def _touch_chat_session(chat_id: int) -> None:
    db = SessionLocal()
    try:
        chat_session = db.query(AIChatSession).filter(
            AIChatSession.id == chat_id
        ).first()
        if chat_session:
            chat_session.updated_at = _utc_now()
            db.commit()
    finally:
        db.close()


def _persist_history_message(
    user_id: int,
    chat_id: int,
    role: str,
    content: Any,
    timestamp: str,
    status: str,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        message = AIChatMessage(
            chat_session_id=chat_id,
            user_id=user_id,
            role=role,
            content=_normalize_json_value(_sync_embedded_status(content, status)),
            extra=_normalize_json_value(extra),
            status=_parse_status(status),
            timestamp=datetime.fromisoformat(timestamp),
            updated_at=_utc_now(),
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        _touch_chat_session(chat_id)
        return _serialize_chat_message(message)
    finally:
        db.close()


def _complete_active_history_in_db(user_id: int, chat_id: int, role: Optional[str] = None) -> None:
    db = SessionLocal()
    try:
        query = db.query(AIChatMessage).filter(
            AIChatMessage.user_id == user_id,
            AIChatMessage.chat_session_id == chat_id,
            AIChatMessage.status == ChatMessageStatus.ACTIVE
        )
        if role:
            query = query.filter(AIChatMessage.role == role)

        active_messages = query.all()
        now = _utc_now()

        for message in active_messages:
            message.status = ChatMessageStatus.COMPLETED
            message.content = _normalize_json_value(
                _sync_embedded_status(
                    message.content,
                    ChatMessageStatus.COMPLETED.value
                )
            )
            message.updated_at = now

        if active_messages:
            db.commit()
            _touch_chat_session(chat_id)
    finally:
        db.close()


def _get_persisted_history(user_id: int, chat_id: Optional[int] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        query = db.query(AIChatMessage).filter(
            AIChatMessage.user_id == user_id
        ).order_by(AIChatMessage.timestamp.asc(), AIChatMessage.id.asc())

        if chat_id is not None:
            query = query.filter(AIChatMessage.chat_session_id == chat_id)

        if limit is not None:
            messages = query.order_by(
                AIChatMessage.timestamp.desc(),
                AIChatMessage.id.desc()
            ).limit(limit).all()
            messages.reverse()
        else:
            messages = query.all()

        return [_serialize_chat_message(message) for message in messages]
    finally:
        db.close()


def _list_chat_sessions(user_id: int) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        sessions = db.query(AIChatSession).filter(
            AIChatSession.user_id == user_id
        ).order_by(AIChatSession.updated_at.desc(), AIChatSession.id.desc()).all()
        return [_serialize_chat_session(chat_session) for chat_session in sessions]
    finally:
        db.close()


def ensure_chat_session(
    user_id: int,
    chat_id: Optional[int] = None,
    initial_message: Optional[Any] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    return _ensure_chat_session(
        user_id,
        chat_id=chat_id,
        initial_message=initial_message,
        title=title,
    )


def list_chat_sessions(user_id: int) -> List[Dict[str, Any]]:
    return _list_chat_sessions(user_id)


def get_session(user_id: int, chat_id: Optional[int] = None) -> Dict[str, Any]:
    return session_store.get(user_id, chat_id=chat_id)


def set_session(user_id: int, data: Dict[str, Any], chat_id: Optional[int] = None, ttl_seconds: Optional[int] = None) -> None:
    session_store.set(user_id, data, chat_id=chat_id, ttl_seconds=ttl_seconds)


def update_session(user_id: int, updates: Dict[str, Any], chat_id: Optional[int] = None, ttl_seconds: Optional[int] = None) -> None:
    session_store.update(user_id, updates, chat_id=chat_id, ttl_seconds=ttl_seconds)


def clear_session(user_id: int, chat_id: Optional[int] = None) -> None:
    session_store.clear(user_id, chat_id=chat_id)


def session_exists(user_id: int, chat_id: Optional[int] = None) -> bool:
    return session_store.exists(user_id, chat_id=chat_id)


def append_history(
    user_id: int,
    chat_id: int,
    role: str,
    content: Any,
    ttl_seconds: Optional[int] = None,
    extra: Optional[Dict[str, Any]] = None,
    status: str = ChatMessageStatus.COMPLETED.value,
) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    normalized_content = _sync_embedded_status(content, status)

    session_store.append_history(
        user_id=user_id,
        chat_id=chat_id,
        role=role,
        content=normalized_content,
        ttl_seconds=ttl_seconds,
        extra=extra,
        status=status,
    )
    _persist_history_message(
        user_id=user_id,
        chat_id=chat_id,
        role=role,
        content=normalized_content,
        timestamp=timestamp,
        status=status,
        extra=extra,
    )


def complete_active_history(
    user_id: int,
    chat_id: int,
    role: Optional[str] = None,
    ttl_seconds: Optional[int] = None,
) -> None:
    session_store.complete_active_history(
        user_id=user_id,
        chat_id=chat_id,
        role=role,
        ttl_seconds=ttl_seconds,
    )
    _complete_active_history_in_db(user_id=user_id, chat_id=chat_id, role=role)


def get_history(user_id: int, chat_id: Optional[int] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    return session_store.get_history(user_id, chat_id=chat_id, limit=limit)


def get_persisted_history(user_id: int, chat_id: Optional[int] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    return _get_persisted_history(user_id, chat_id=chat_id, limit=limit)


def set_state(user_id: int, state: str, chat_id: Optional[int] = None, ttl_seconds: Optional[int] = None) -> None:
    session_store.set_state(user_id, state, chat_id=chat_id, ttl_seconds=ttl_seconds)


def get_state(user_id: int, chat_id: Optional[int] = None) -> str:
    return session_store.get_state(user_id, chat_id=chat_id)


def set_context(
    user_id: int,
    chat_id: Optional[int] = None,
    *,
    doctor_id: Optional[int] = None,
    hospital_id: Optional[int] = None,
    department_id: Optional[int] = None,
    ttl_seconds: Optional[int] = None,
) -> None:
    session_store.set_context(
        user_id,
        chat_id=chat_id,
        doctor_id=doctor_id,
        hospital_id=hospital_id,
        department_id=department_id,
        ttl_seconds=ttl_seconds,
    )


def get_context(user_id: int, chat_id: Optional[int] = None) -> Dict[str, Any]:
    return session_store.get_context(user_id, chat_id=chat_id)


def set_message_context(
    user_id: int,
    chat_id: Optional[int] = None,
    user_message: Optional[str] = None,
    ai_message: Optional[str] = None,
    ttl_seconds: Optional[int] = None,
) -> None:
    session_store.set_message_context(
        user_id,
        chat_id=chat_id,
        user_message=user_message,
        ai_message=ai_message,
        ttl_seconds=ttl_seconds,
    )
