"""
MedCode AI V19 — Authentication Middleware for FastAPI
======================================================
Integrates JWT authentication with FastAPI routes.
"""

from __future__ import annotations

from typing import Callable, List, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from security.auth import get_auth_service


# Paths that don't require authentication
PUBLIC_PATHS = {
    "/api/v19/dashboard/stats",
    "/api/v19/dashboard/activity",
    "/api/v19/dashboard/charts",
    "/api/v19/auth/stats",
    "/",
    "/health",
    "/ready",
    "/live",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/static",
    "/metrics",
    "/metrics/json",
    "/pipeline/stages",
    "/code",
    "/batch",
    "/api/v19/auth/login",
    "/api/v19/auth/register",
    "/api/v19/auth/refresh",
    "/api/v19/auth/emergency-access",
    "/api/v19/auth/emergency-access/active",
}

# Path prefixes that don't require authentication
PUBLIC_PREFIXES = {
    "/static/",
}


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    JWT authentication middleware.
    Validates Bearer tokens on protected routes.
    """

    def __init__(self, app, public_paths: Optional[List[str]] = None, enabled: bool = True):
        super().__init__(app)
        self._enabled = enabled
        self._public_paths = PUBLIC_PATHS.copy()
        if public_paths:
            self._public_paths.update(public_paths)

    def _is_public_path(self, path: str) -> bool:
        for public in self._public_paths:
            if path == public or path.startswith(public + "/"):
                return True
        for prefix in PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return True
        return False

    async def dispatch(self, request: Request, call_next):
        if not self._enabled:
            return await call_next(request)

        path = request.url.path

        if self._is_public_path(path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "error": "authentication_required",
                    "message": "Valid Bearer token required",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header[7:]
        auth_service = get_auth_service()
        payload = auth_service.validate_token(token)

        if payload is None:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "invalid_token",
                    "message": "Token is invalid or expired",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        request.state.user_id = payload.user_id
        request.state.user_role = payload.role
        request.state.user_token = token
        request.state.provider_id = payload.provider_id

        return await call_next(request)


def require_permission(permission: str):
    """Dependency factory: require a specific permission."""
    async def dependency(request: Request):
        token = getattr(request.state, "user_token", "")
        if not token:
            return JSONResponse(
                status_code=401,
                content={"error": "authentication_required"},
            )
        auth_service = get_auth_service()
        if not auth_service.check_permission(token, permission):
            return JSONResponse(
                status_code=403,
                content={
                    "error": "permission_denied",
                    "message": f"Permission '{permission}' required",
                },
            )
    return dependency
