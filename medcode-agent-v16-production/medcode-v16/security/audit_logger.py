"""
MedCode AI — HIPAA Audit Logger
=================================
Structured audit events for HIPAA compliance.
Writes to both file-based audit_log and in-memory store.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger("medcode.audit")


@dataclass
class AuditEvent:
    """Structured audit event for HIPAA compliance."""
    event_id: str = ""
    timestamp: float = 0.0
    user_id: str = ""
    role: str = ""
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    ip_address: str = ""
    success: bool = True
    details: str = ""
    request_id: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["timestamp_iso"] = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.timestamp)
        )
        return d


class AuditEventStore:
    """In-memory store for audit events with file-backed persistence."""

    def __init__(self, max_events: int = 10000):
        self._events: List[AuditEvent] = []
        self._max_events = max_events

    def append(self, event: AuditEvent) -> None:
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

    def get_events(
        self,
        limit: int = 100,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[AuditEvent]:
        filtered = self._events
        if action:
            filtered = [e for e in filtered if e.action == action]
        if user_id:
            filtered = [e for e in filtered if e.user_id == user_id]
        return filtered[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        from collections import Counter
        action_counts = Counter(e.action for e in self._events)
        return {
            "total_events": len(self._events),
            "by_action": dict(action_counts),
        }


_store = AuditEventStore()


def get_audit_store() -> AuditEventStore:
    return _store


def log_audit_event(
    action: str,
    user_id: str = "",
    role: str = "",
    resource_type: str = "",
    resource_id: str = "",
    ip_address: str = "",
    success: bool = True,
    details: str = "",
    request_id: str = "",
) -> AuditEvent:
    """
    Log a structured HIPAA audit event.
    Writes to both logger and in-memory store.
    """
    event = AuditEvent(
        event_id=str(uuid.uuid4()),
        timestamp=time.time(),
        user_id=user_id,
        role=role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        success=success,
        details=details,
        request_id=request_id,
    )

    logger.info(
        "audit_event",
        extra={
            "audit_event": event.to_dict(),
        },
    )

    _store.append(event)

    return event


def log_login(user_id: str, role: str, ip_address: str, success: bool, request_id: str = "") -> AuditEvent:
    action = "login_success" if success else "login_failed"
    return log_audit_event(
        action=action,
        user_id=user_id,
        role=role,
        resource_type="auth",
        ip_address=ip_address,
        success=success,
        request_id=request_id,
    )


def log_logout(user_id: str, role: str, request_id: str = "") -> AuditEvent:
    return log_audit_event(
        action="logout",
        user_id=user_id,
        role=role,
        resource_type="auth",
        success=True,
        request_id=request_id,
    )


def log_phi_access(user_id: str, role: str, resource_type: str, resource_id: str, ip_address: str, request_id: str = "") -> AuditEvent:
    return log_audit_event(
        action="access_phi",
        user_id=user_id,
        role=role,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        success=True,
        request_id=request_id,
    )


def log_data_modification(user_id: str, role: str, resource_type: str, resource_id: str, ip_address: str, details: str = "", request_id: str = "") -> AuditEvent:
    return log_audit_event(
        action="modify_data",
        user_id=user_id,
        role=role,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        success=True,
        details=details,
        request_id=request_id,
    )


def log_emergency_access(user_id: str, role: str, reason: str, ip_address: str, success: bool, request_id: str = "") -> AuditEvent:
    return log_audit_event(
        action="emergency_access",
        user_id=user_id,
        role=role,
        resource_type="auth",
        ip_address=ip_address,
        success=success,
        details=reason,
        request_id=request_id,
    )
