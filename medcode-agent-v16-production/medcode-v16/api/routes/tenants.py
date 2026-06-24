"""
MedCode AI V19 — Tenant API Routes
=====================================
REST endpoints for managing tenants (organizations).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

router = APIRouter(prefix="/api/v19/tenants", tags=["tenants"])


class CreateTenantRequest(BaseModel):
    name: str
    plan: str = "free"
    settings: Optional[Dict[str, Any]] = None


class UpdateTenantRequest(BaseModel):
    name: Optional[str] = None
    plan: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class TenantResponse(BaseModel):
    id: str
    name: str
    plan: str
    settings: Dict[str, Any] = {}
    active: bool
    created_at: str
    updated_at: str


@router.post("", response_model=TenantResponse)
async def create_tenant(body: CreateTenantRequest):
    """Create a new tenant (admin only)."""
    from core.tenant import TenantManager

    manager = TenantManager()
    tenant = manager.create_tenant(
        name=body.name,
        plan=body.plan,
        settings=body.settings,
    )
    return TenantResponse(**tenant)


@router.get("", response_model=List[TenantResponse])
async def list_tenants():
    """List all active tenants (admin only)."""
    from core.tenant import TenantManager

    manager = TenantManager()
    tenants = manager.list_tenants()
    return [TenantResponse(**t) for t in tenants]


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str):
    """Get tenant details."""
    from core.tenant import TenantManager

    manager = TenantManager()
    tenant = manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantResponse(**tenant)


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: str, body: UpdateTenantRequest):
    """Update tenant settings."""
    from core.tenant import TenantManager

    manager = TenantManager()
    tenant = manager.update_tenant(
        tenant_id=tenant_id,
        name=body.name,
        plan=body.plan,
        settings=body.settings,
    )
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantResponse(**tenant)


@router.delete("/{tenant_id}")
async def delete_tenant(tenant_id: str):
    """Soft-delete a tenant (admin only)."""
    from core.tenant import TenantManager

    manager = TenantManager()
    removed = manager.delete_tenant(tenant_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"status": "deleted", "tenant_id": tenant_id}
