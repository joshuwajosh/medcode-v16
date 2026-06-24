"""
MedCode AI V19 — Tenant Middleware
===================================
FastAPI middleware that extracts tenant from JWT token and sets
tenant context for every request. Enforces row-level isolation.
"""
from __future__ import annotations

import json
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.tenant import TenantContext


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Extracts organization_id from the JWT token (Authorization header)
    and sets it as the current tenant for the duration of the request.

    The tenant_id is stored in request.state.tenant_id for downstream use.
    If no JWT is present or the token lacks organization_id, the request
    proceeds without tenant context (public/admin endpoints remain accessible).
    """

    EXEMPT_PATHS = {
        "/health",
        "/v1/health",
        "/ready",
        "/v1/ready",
        "/live",
        "/v1/live",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path

        if path in self.EXEMPT_PATHS or path.startswith("/static") or path.startswith("/dashboard"):
            return await call_next(request)

        tenant_id = self._extract_tenant(request)

        TenantContext.set_current_tenant(tenant_id)
        request.state.tenant_id = tenant_id

        try:
            response = await call_next(request)
        finally:
            TenantContext.set_current_tenant(None)

        return response

    def _extract_tenant(self, request: Request) -> Optional[str]:
        """Extract tenant_id from the Authorization header JWT."""
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]
        try:
            payload = _decode_jwt_payload(token)
            return payload.get("organization_id") or payload.get("tenant_id")
        except Exception:
            return None


def _decode_jwt_payload(token: str) -> dict:
    """
    Decode the payload portion of a JWT without verification.
    This is used for extracting tenant context; actual auth verification
    is handled by the AuthenticationMiddleware.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")

    import base64
    payload_b64 = parts[1]
    # Add padding
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding

    decoded = base64.urlsafe_b64decode(payload_b64)
    return json.loads(decoded)
