"""
MedCode AI V19 — Webhook Data Models
=====================================
Dataclasses for webhook registration, event tracking, and delivery logging.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


VALID_WEBHOOK_EVENTS = [
    "claim.submitted",
    "claim.acknowledged",
    "claim.paid",
    "claim.denied",
    "claim.appealed",
]


@dataclass
class Webhook:
    """Registered webhook endpoint."""
    id: str = ""
    organization_id: str = ""
    url: str = ""
    events: List[str] = field(default_factory=list)
    secret: str = ""
    active: bool = True
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "url": self.url,
            "events": self.events,
            "active": self.active,
            "created_at": self.created_at,
        }


@dataclass
class WebhookEvent:
    """A single webhook event attempt record."""
    webhook_id: str = ""
    event_type: str = ""
    payload: Optional[dict] = None
    status: str = "pending"  # pending | sent | failed
    attempts: int = 0
    last_error: str = ""

    def to_dict(self) -> dict:
        return {
            "webhook_id": self.webhook_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "status": self.status,
            "attempts": self.attempts,
            "last_error": self.last_error,
        }


@dataclass
class WebhookDelivery:
    """Delivery log entry for a webhook event."""
    id: str = ""
    webhook_id: str = ""
    event_type: str = ""
    status: str = "pending"  # pending | sent | failed
    response_code: Optional[int] = None
    delivered_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "webhook_id": self.webhook_id,
            "event_type": self.event_type,
            "status": self.status,
            "response_code": self.response_code,
            "delivered_at": self.delivered_at,
        }
