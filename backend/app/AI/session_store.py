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
from typing import Any, Dict, List, Optional


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
        self._store: Dict[int, Dict[str, Any]] = {}
        self._expiry: Dict[int, float] = {}
        self._lock = threading.Lock()
        self.default_ttl_seconds = default_ttl_seconds

    def _now(self) -> float:
        return time.time()

    def _utc_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _is_expired(self, user_id: int) -> bool:
        expiry = self._expiry.get(user_id)
        if expiry is None:
            return False
        return self._now() > expiry

    def _cleanup_if_expired(self, user_id: int) -> None:
        if self._is_expired(user_id):
            self._store.pop(user_id, None)
            self._expiry.pop(user_id, None)

    def _touch(self, user_id: int, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        self._expiry[user_id] = self._now() + ttl

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

    def ensure(self, user_id: int, ttl_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        Ensure a session exists for the user and return a copy of it.
        """
        with self._lock:
            self._cleanup_if_expired(user_id)
            if user_id not in self._store:
                self._store[user_id] = self._create_base_session()
                self._touch(user_id, ttl_seconds)
            return deepcopy(self._store[user_id])

    def get(self, user_id: int) -> Dict[str, Any]:
        """
        Return the current session for the user.
        If no session exists or it expired, return an empty dict.
        """
        with self._lock:
            self._cleanup_if_expired(user_id)
            if user_id not in self._store:
                return {}
            return deepcopy(self._store[user_id])

    def set(self, user_id: int, data: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        """
        Replace the whole session for a user.
        """
        with self._lock:
            current = self._create_base_session()
            current.update(deepcopy(data))
            current["updated_at"] = self._utc_timestamp()
            if "created_at" not in current or current["created_at"] is None:
                current["created_at"] = self._utc_timestamp()

            self._store[user_id] = current
            self._touch(user_id, ttl_seconds)

    def update(self, user_id: int, updates: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        """
        Merge updates into the current session.
        If the session does not exist, it is created first.
        """
        with self._lock:
            self._cleanup_if_expired(user_id)

            if user_id not in self._store:
                self._store[user_id] = self._create_base_session()

            for key, value in deepcopy(updates).items():
                self._store[user_id][key] = value

            self._store[user_id]["updated_at"] = self._utc_timestamp()
            self._touch(user_id, ttl_seconds)

    def set_state(self, user_id: int, state: str, ttl_seconds: Optional[int] = None) -> None:
        """
        Convenience helper to update only the conversation state.
        """
        self.update(user_id, {"state": state}, ttl_seconds=ttl_seconds)

    def get_state(self, user_id: int) -> str:
        """
        Return the current state for a user.
        Falls back to 'idle' if no session exists.
        """
        session = self.get(user_id)
        return session.get("state", "idle")

    def set_flow(self, user_id: int, flow: Optional[str], ttl_seconds: Optional[int] = None) -> None:
        self.update(user_id, {"flow": flow}, ttl_seconds=ttl_seconds)

    def append_history(
        self,
        user_id: int,
        role: str,
        content: str,
        ttl_seconds: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Append one message to the active session history.

        role should usually be 'user' or 'assistant'.
        """
        with self._lock:
            self._cleanup_if_expired(user_id)

            if user_id not in self._store:
                self._store[user_id] = self._create_base_session()

            message = {
                "role": role,
                "content": content,
                "timestamp": self._utc_timestamp(),
            }

            if extra:
                message["extra"] = deepcopy(extra)

            self._store[user_id].setdefault("history", [])
            self._store[user_id]["history"].append(message)
            self._store[user_id]["updated_at"] = self._utc_timestamp()
            self._touch(user_id, ttl_seconds)

    def get_history(self, user_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Return the conversation history for a user.
        If limit is provided, return only the most recent messages.
        """
        session = self.get(user_id)
        history = session.get("history", [])
        if limit is None:
            return deepcopy(history)
        return deepcopy(history[-limit:])

    def set_entities(self, user_id: int, entities: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        self.update(user_id, {"entities": deepcopy(entities)}, ttl_seconds=ttl_seconds)

    def get_entities(self, user_id: int) -> Dict[str, Any]:
        session = self.get(user_id)
        return deepcopy(session.get("entities", {}))

    def set_context(
        self,
        user_id: int,
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
            self.update(user_id, updates, ttl_seconds=ttl_seconds)

    def get_context(self, user_id: int) -> Dict[str, Any]:
        session = self.get(user_id)
        return {
            "doctor_id": session.get("doctor_id"),
            "hospital_id": session.get("hospital_id"),
            "department_id": session.get("department_id"),
        }

    def set_message_context(
        self,
        user_id: int,
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
            self.update(user_id, updates, ttl_seconds=ttl_seconds)

    def clear(self, user_id: int) -> None:
        """
        Remove a user's session completely.
        """
        with self._lock:
            self._store.pop(user_id, None)
            self._expiry.pop(user_id, None)

    def exists(self, user_id: int) -> bool:
        with self._lock:
            self._cleanup_if_expired(user_id)
            return user_id in self._store

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


def get_session(user_id: int) -> Dict[str, Any]:
    return session_store.get(user_id)


def set_session(user_id: int, data: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
    session_store.set(user_id, data, ttl_seconds=ttl_seconds)


def update_session(user_id: int, updates: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
    session_store.update(user_id, updates, ttl_seconds=ttl_seconds)


def clear_session(user_id: int) -> None:
    session_store.clear(user_id)


def session_exists(user_id: int) -> bool:
    return session_store.exists(user_id)


def append_history(
    user_id: int,
    role: str,
    content: str,
    ttl_seconds: Optional[int] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    session_store.append_history(
        user_id=user_id,
        role=role,
        content=content,
        ttl_seconds=ttl_seconds,
        extra=extra,
    )


def get_history(user_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    return session_store.get_history(user_id, limit=limit)


def set_state(user_id: int, state: str, ttl_seconds: Optional[int] = None) -> None:
    session_store.set_state(user_id, state, ttl_seconds=ttl_seconds)


def get_state(user_id: int) -> str:
    return session_store.get_state(user_id)


def set_context(
    user_id: int,
    *,
    doctor_id: Optional[int] = None,
    hospital_id: Optional[int] = None,
    department_id: Optional[int] = None,
    ttl_seconds: Optional[int] = None,
) -> None:
    session_store.set_context(
        user_id,
        doctor_id=doctor_id,
        hospital_id=hospital_id,
        department_id=department_id,
        ttl_seconds=ttl_seconds,
    )


def get_context(user_id: int) -> Dict[str, Any]:
    return session_store.get_context(user_id)


def set_message_context(
    user_id: int,
    user_message: Optional[str] = None,
    ai_message: Optional[str] = None,
    ttl_seconds: Optional[int] = None,
) -> None:
    session_store.set_message_context(
        user_id,
        user_message=user_message,
        ai_message=ai_message,
        ttl_seconds=ttl_seconds,
    )