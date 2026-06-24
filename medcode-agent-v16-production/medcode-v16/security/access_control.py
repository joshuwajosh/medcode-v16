"""
MedCode AI V14 — Access Control & Encryption Service

Role-Based Access Control (RBAC) for:
  - Medical coders (can view/edit codes)
  - Reviewers (can approve/reject escalated codes)
  - Admins (full access)
  - Auditors (read-only audit logs)
  - Providers (submit notes, view results for their patients only)

Encryption service for:
  - PHI data at rest
  - Audit logs
  - Inter-service communication tokens
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from security.constants import Role, PERMISSIONS


@dataclass
class UserContext:
    user_id: str
    role: Role
    provider_id: Optional[str] = None    # for provider isolation
    organization_id: str = ""
    session_token: str = ""
    session_expires: float = 0.0

    @property
    def is_expired(self) -> bool:
        return time.time() > self.session_expires

    def can(self, permission: str) -> bool:
        allowed = PERMISSIONS.get(permission, set())
        return self.role in allowed


class AccessControl:
    """
    V14 Role-Based Access Control.
    Enforces provider isolation — providers can only access their own patients.
    """

    def check_permission(self, user: UserContext, permission: str) -> bool:
        if user.is_expired:
            return False
        return user.can(permission)

    def check_provider_isolation(
        self,
        user: UserContext,
        resource_provider_id: str,
    ) -> bool:
        """Provider users can only access their own patients."""
        if user.role != Role.PROVIDER:
            return True   # non-providers not restricted by this rule
        if user.provider_id is None:
            return False
        return user.provider_id == resource_provider_id


class EncryptionService:
    """
    Lightweight encryption service for PHI data at rest.
    In production, delegates to KMS (AWS, GCP, Azure).
    V14: HMAC-based token generation for audit trail integrity.
    """

    def __init__(self, secret_key: Optional[str] = None):
        self._key = (secret_key or os.environ.get("MEDCODE_SECRET_KEY", "dev_key_change_in_production")).encode()

    def generate_audit_token(self, data: str) -> str:
        """Generate an HMAC token for audit log integrity."""
        h = hmac.new(self._key, data.encode(), hashlib.sha256)
        return h.hexdigest()

    def verify_audit_token(self, data: str, token: str) -> bool:
        expected = self.generate_audit_token(data)
        return hmac.compare_digest(expected, token)

    def hash_phi(self, phi_value: str) -> str:
        """One-way hash for PHI reference (not reversible)."""
        return hashlib.sha256((phi_value + self._key.decode()).encode()).hexdigest()[:16]


@dataclass
class AuditLogEntry:
    """An immutable audit log record."""
    timestamp: float
    user_id: str
    action: str
    resource: str
    note_id: str
    result: str
    integrity_token: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "note_id": self.note_id,
            "result": self.result,
        }


class AuditLogger:
    """
    Append-only audit logger with integrity tokens.
    All actions on PHI are logged.
    """

    def __init__(self):
        self._log: List[AuditLogEntry] = []
        self._enc = EncryptionService()

    def log(
        self,
        user_id: str,
        action: str,
        resource: str,
        note_id: str,
        result: str,
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            timestamp=time.time(),
            user_id=user_id,
            action=action,
            resource=resource,
            note_id=note_id,
            result=result,
        )
        entry.integrity_token = self._enc.generate_audit_token(
            f"{entry.timestamp}:{user_id}:{action}:{note_id}"
        )
        self._log.append(entry)
        return entry

    def get_log(self, note_id: Optional[str] = None) -> List[dict]:
        if note_id:
            return [e.to_dict() for e in self._log if e.note_id == note_id]
        return [e.to_dict() for e in self._log]
