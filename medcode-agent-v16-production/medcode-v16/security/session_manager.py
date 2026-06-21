"""
MedCode AI V19 — Session Manager with Automatic Logoff
========================================================
HIPAA §164.312(a)(2)(iii) — Automatic Logoff.
HIPAA §164.312(a)(2)(i) — Unique User Identification.

Manages user sessions with:
  - Inactive session timeout (15 minutes default)
  - Absolute session timeout (8 hours)
  - Session activity tracking
  - Automatic cleanup of expired sessions
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class SessionInfo:
    """User session information."""
    session_id: str = ""
    user_id: str = ""
    role: str = ""
    created_at: float = 0.0
    last_activity: float = 0.0
    expires_at: float = 0.0
    inactive_timeout: float = 900.0  # 15 minutes default
    ip_address: str = ""
    user_agent: str = ""
    is_active: bool = True

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def idle_seconds(self) -> float:
        return time.time() - self.last_activity

    @property
    def is_idle(self) -> bool:
        return self.idle_seconds > self.inactive_timeout

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "role": self.role,
            "created_at": datetime.fromtimestamp(self.created_at, tz=timezone.utc).isoformat(),
            "last_activity": datetime.fromtimestamp(self.last_activity, tz=timezone.utc).isoformat(),
            "expires_at": datetime.fromtimestamp(self.expires_at, tz=timezone.utc).isoformat(),
            "is_active": self.is_active,
            "is_expired": self.is_expired,
            "is_idle": self.is_idle,
            "idle_seconds": round(self.idle_seconds),
        }


class SessionManager:
    """
    Server-side session management with automatic logoff.
    
    Features:
      - Inactive session timeout (configurable, default 15 min)
      - Absolute session timeout (configurable, default 8 hours)
      - Session activity tracking
      - Automatic cleanup of expired sessions
      - Session invalidation on logout
    """

    def __init__(
        self,
        inactive_timeout_minutes: int = 15,
        absolute_timeout_hours: int = 8,
    ):
        self._sessions: Dict[str, SessionInfo] = {}
        self._inactive_timeout = inactive_timeout_minutes * 60
        self._absolute_timeout = absolute_timeout_hours * 3600

    def create_session(
        self,
        user_id: str,
        role: str = "",
        ip_address: str = "",
        user_agent: str = "",
    ) -> SessionInfo:
        """Create a new user session."""
        now = time.time()
        session = SessionInfo(
            session_id=str(uuid.uuid4())[:12],
            user_id=user_id,
            role=role,
            created_at=now,
            last_activity=now,
            expires_at=now + self._absolute_timeout,
            inactive_timeout=self._inactive_timeout,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get a session by ID, checking for expiry and inactivity."""
        session = self._sessions.get(session_id)
        if session is None:
            return None

        if not session.is_active:
            return None

        if session.is_expired:
            session.is_active = False
            return None

        if session.is_idle:
            session.is_active = False
            return None

        return session

    def touch_session(self, session_id: str) -> bool:
        """Update session activity timestamp."""
        session = self._sessions.get(session_id)
        if session is None or not session.is_active:
            return False
        if session.is_expired:
            session.is_active = False
            return False

        session.last_activity = time.time()
        return True

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session (logout)."""
        session = self._sessions.get(session_id)
        if session:
            session.is_active = False
            return True
        return False

    def invalidate_user_sessions(self, user_id: str) -> int:
        """Invalidate all sessions for a user."""
        count = 0
        for session in self._sessions.values():
            if session.user_id == user_id and session.is_active:
                session.is_active = False
                count += 1
        return count

    def cleanup_expired(self) -> int:
        """Remove expired sessions. Returns count removed."""
        expired_ids = []
        for sid, session in self._sessions.items():
            if session.is_expired or session.is_idle:
                session.is_active = False
                expired_ids.append(sid)

        for sid in expired_ids:
            del self._sessions[sid]

        return len(expired_ids)

    def get_active_sessions(self) -> List[SessionInfo]:
        """Get all active (non-expired) sessions."""
        return [
            s for s in self._sessions.values()
            if s.is_active and not s.is_expired and not s.is_idle
        ]

    def get_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """Get all sessions for a user."""
        return [
            s for s in self._sessions.values()
            if s.user_id == user_id
        ]

    def get_stats(self) -> dict:
        active = self.get_active_sessions()
        return {
            "total_sessions": len(self._sessions),
            "active_sessions": len(active),
            "inactive_timeout_minutes": self._inactive_timeout // 60,
            "absolute_timeout_hours": self._absolute_timeout // 3600,
        }


_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
