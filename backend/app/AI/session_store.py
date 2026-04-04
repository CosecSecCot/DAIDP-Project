# ai/session_store.py

"""
Production-ready session store for AI conversational state.

Features:
- Thread-safe in-memory store
- TTL (auto-expiry)
- Clean API
- Easy migration to Redis

NOTE:
For production scaling (multiple servers), replace this with Redis.
"""

import threading
import time
from typing import Dict, Any, Optional


class SessionStore:
    """
    Thread-safe session store with TTL support.
    """

    def __init__(self, default_ttl_seconds: int = 600):
        """
        Args:
            default_ttl_seconds: session expiry time (default = 10 minutes)
        """
        self._store: Dict[int, Dict[str, Any]] = {}
        self._expiry: Dict[int, float] = {}
        self._lock = threading.Lock()
        self.default_ttl = default_ttl_seconds

    # ===============================
    # INTERNAL METHODS
    # ===============================

    def _is_expired(self, user_id: int) -> bool:
        expiry = self._expiry.get(user_id)
        if not expiry:
            return False
        return time.time() > expiry

    def _cleanup_if_expired(self, user_id: int):
        if self._is_expired(user_id):
            self._store.pop(user_id, None)
            self._expiry.pop(user_id, None)

    # ===============================
    # PUBLIC METHODS
    # ===============================

    def get(self, user_id: int) -> Dict[str, Any]:
        """
        Get session data for a user.

        Returns empty dict if:
        - session does not exist
        - session expired
        """
        with self._lock:
            self._cleanup_if_expired(user_id)
            return self._store.get(user_id, {}).copy()

    def set(self, user_id: int, data: Dict[str, Any], ttl: Optional[int] = None):
        """
        Create or overwrite session.

        Args:
            user_id: user identifier
            data: session dictionary
            ttl: custom TTL (seconds)
        """
        with self._lock:
            self._store[user_id] = data.copy()
            self._expiry[user_id] = time.time() + (ttl or self.default_ttl)

    def update(self, user_id: int, updates: Dict[str, Any], ttl: Optional[int] = None):
        """
        Update existing session (merge).

        If session does not exist → create new
        """
        with self._lock:
            self._cleanup_if_expired(user_id)

            existing = self._store.get(user_id, {})
            existing.update(updates)

            self._store[user_id] = existing
            self._expiry[user_id] = time.time() + (ttl or self.default_ttl)

    def delete(self, user_id: int):
        """
        Remove session completely
        """
        with self._lock:
            self._store.pop(user_id, None)
            self._expiry.pop(user_id, None)

    def clear_all(self):
        """
        Clear all sessions (admin/debug)
        """
        with self._lock:
            self._store.clear()
            self._expiry.clear()

    def exists(self, user_id: int) -> bool:
        """
        Check if session exists and not expired
        """
        with self._lock:
            self._cleanup_if_expired(user_id)
            return user_id in self._store


# ===============================
# SINGLETON INSTANCE
# ===============================

session_store = SessionStore()


# ===============================
# HELPER FUNCTIONS (CLEAN API)
# ===============================

def get_session(user_id: int) -> Dict[str, Any]:
    return session_store.get(user_id)


def set_session(user_id: int, data: Dict[str, Any]):
    session_store.set(user_id, data)


def update_session(user_id: int, updates: Dict[str, Any]):
    session_store.update(user_id, updates)


def clear_session(user_id: int):
    session_store.delete(user_id)


def session_exists(user_id: int) -> bool:
    return session_store.exists(user_id)