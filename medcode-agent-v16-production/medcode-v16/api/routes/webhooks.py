"""
MedCode AI V19 — Webhook API Routes
====================================
REST endpoints for managing webhook registrations and delivery history.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

router = APIRouter(prefix="/api/v19/webhooks", tags=["webhooks"])


class RegisterWebhookRequest(BaseModel):
    organization_id: str
    url: str
    events: List[str]
    secret: str


class WebhookResponse(BaseModel):
    id: str
    organization_id: str
    url: str
    events: List[str]
    active: bool
    created_at: str


class DeliveryResponse(BaseModel):
    id: str
    webhook_id: str
    event_type: str
    status: str
    response_code: Optional[int] = None
    delivered_at: Optional[str] = None


@router.post("", response_model=WebhookResponse)
async def register_webhook(body: RegisterWebhookRequest) -> WebhookResponse:
    """Register a new webhook endpoint for claim status events."""
    from billing.webhook_manager import WebhookManager

    manager = WebhookManager()
    try:
        webhook = manager.register_webhook(
            organization_id=body.organization_id,
            url=body.url,
            events=body.events,
            secret=body.secret,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return WebhookResponse(**webhook.to_dict())


@router.get("", response_model=List[WebhookResponse])
async def list_webhooks(organization_id: str) -> List[WebhookResponse]:
    """List all active webhooks for an organization."""
    from billing.webhook_manager import WebhookManager

    manager = WebhookManager()
    webhooks = manager.list_webhooks(organization_id)
    return [WebhookResponse(**w.to_dict()) for w in webhooks]


@router.delete("/{webhook_id}")
async def unregister_webhook(webhook_id: str) -> Dict[str, str]:
    """Deactivate a webhook."""
    from billing.webhook_manager import WebhookManager

    manager = WebhookManager()
    removed = manager.unregister_webhook(webhook_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"status": "removed", "webhook_id": webhook_id}


@router.get("/{webhook_id}/deliveries", response_model=List[DeliveryResponse])
async def get_deliveries(webhook_id: str, limit: int = 50) -> List[DeliveryResponse]:
    """Get delivery history for a webhook."""
    from billing.webhook_manager import WebhookManager

    manager = WebhookManager()
    deliveries = manager.get_deliveries(webhook_id, limit=limit)
    return [DeliveryResponse(**d.to_dict()) for d in deliveries]
