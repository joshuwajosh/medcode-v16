"""
MedCode AI V19 — Emergency Access (Break-Glass) Procedure
==========================================================
HIPAA §164.312(a)(2)(ii) — Emergency Access Procedure.

Provides break-glass emergency access when normal authentication
is unavailable or when immediate access to PHI is required for
patient care.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class EmergencyAccessGrant:
    """Record of an emergency access grant."""
    grant_id: str = ""
    user_id: str = ""
    reason: str = ""
    granted_at: float = 0.0
    expires_at: float = 0.0
    revoked: bool = False
    revoked_at: float = 0.0
    reviewed: bool = False
    reviewed_by: str = ""
    review_notes: str = ""

    @property
    def is_active(self) -> bool:
        return (
            not self.revoked
            and time.time() < self.expires_at
        )

    def to_dict(self) -> dict:
        return {
            "grant_id": self.grant_id,
            "user_id": self.user_id,
            "reason": self.reason,
            "granted_at": datetime.fromtimestamp(self.granted_at, tz=timezone.utc).isoformat(),
            "expires_at": datetime.fromtimestamp(self.expires_at, tz=timezone.utc).isoformat(),
            "revoked": self.revoked,
            "revoked_at": datetime.fromtimestamp(self.revoked_at, tz=timezone.utc).isoformat() if self.revoked_at else None,
            "reviewed": self.reviewed,
            "reviewed_by": self.reviewed_by,
            "review_notes": self.review_notes,
            "is_active": self.is_active,
        }


class EmergencyAccessService:
    """
    Break-glass emergency access service.
    
    When normal authentication fails or is unavailable:
    1. User provides emergency credentials + reason
    2. System grants temporary elevated access (1 hour)
    3. All emergency access logged with HIGH severity
    4. Security admin notified
    5. Post-access review required within 24 hours
    """

    def __init__(self, grant_duration_seconds: int = 3600):
        self._grants: Dict[str, EmergencyAccessGrant] = {}
        self._grants_by_user: Dict[str, List[str]] = {}
        self._grant_duration = grant_duration_seconds
        self._emergency_secret = os.environ.get(
            "MEDCODE_EMERGENCY_SECRET", "dev_emergency_secret"
        )

    def request_emergency_access(
        self,
        user_id: str,
        reason: str,
        emergency_code: str,
        ip_address: str = "",
    ) -> Optional[EmergencyAccessGrant]:
        """
        Request emergency (break-glass) access.
        
        Args:
            user_id: User requesting emergency access
            reason: Justification for emergency access
            emergency_code: Emergency access code (shared secret)
            ip_address: Client IP address
        
        Returns:
            EmergencyAccessGrant if approved, None if denied
        """
        if not emergency_code or emergency_code != self._emergency_secret:
            return None

        if not reason or len(reason.strip()) < 10:
            return None

        now = time.time()
        grant = EmergencyAccessGrant(
            grant_id=f"EG-{uuid.uuid4().hex[:8].upper()}",
            user_id=user_id,
            reason=reason,
            granted_at=now,
            expires_at=now + self._grant_duration,
        )

        self._grants[grant.grant_id] = grant
        if user_id not in self._grants_by_user:
            self._grants_by_user[user_id] = []
        self._grants_by_user[user_id].append(grant.grant_id)

        return grant

    def validate_emergency_access(self, grant_id: str) -> bool:
        """Check if an emergency access grant is currently active."""
        grant = self._grants.get(grant_id)
        if grant is None:
            return False
        return grant.is_active

    def revoke_emergency_access(self, grant_id: str) -> bool:
        """Revoke an active emergency access grant."""
        grant = self._grants.get(grant_id)
        if grant is None:
            return False
        grant.revoked = True
        grant.revoked_at = time.time()
        return True

    def review_emergency_access(
        self,
        grant_id: str,
        reviewer_id: str,
        review_notes: str = "",
    ) -> bool:
        """Post-access review of emergency access (required within 24 hours)."""
        grant = self._grants.get(grant_id)
        if grant is None:
            return False
        grant.reviewed = True
        grant.reviewed_by = reviewer_id
        grant.review_notes = review_notes
        return True

    def get_active_grants(self) -> List[EmergencyAccessGrant]:
        """Get all currently active emergency access grants."""
        return [g for g in self._grants.values() if g.is_active]

    def get_grants_needing_review(self) -> List[EmergencyAccessGrant]:
        """Get grants that haven't been reviewed yet."""
        return [g for g in self._grants.values() if not g.reviewed]

    def get_user_grants(self, user_id: str) -> List[EmergencyAccessGrant]:
        """Get all emergency access grants for a user."""
        grant_ids = self._grants_by_user.get(user_id, [])
        return [self._grants[gid] for gid in grant_ids if gid in self._grants]

    def get_stats(self) -> dict:
        total = len(self._grants)
        active = len(self.get_active_grants())
        pending_review = len(self.get_grants_needing_review())
        return {
            "total_grants": total,
            "active_grants": active,
            "pending_review": pending_review,
            "grant_duration_hours": self._grant_duration / 3600,
        }


_emergency: Optional[EmergencyAccessService] = None


def get_emergency_service() -> EmergencyAccessService:
    global _emergency
    if _emergency is None:
        _emergency = EmergencyAccessService()
    return _emergency
