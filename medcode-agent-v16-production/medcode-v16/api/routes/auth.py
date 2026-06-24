"""
MedCode AI V19 — Authentication API Routes
============================================
HIPAA-compliant authentication endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from security.auth import get_auth_service, Role
from security.session_manager import get_session_manager
from security.emergency_access import get_emergency_service
from security.audit_store import get_audit_store

router = APIRouter(prefix="/api/v19/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "read_only"
    provider_id: str = ""
    organization_id: str = ""


class RefreshRequest(BaseModel):
    refresh_token: str


class EmergencyAccessRequest(BaseModel):
    user_id: str
    reason: str
    emergency_code: str


class ReviewEmergencyRequest(BaseModel):
    grant_id: str
    review_notes: str = ""


@router.post("/login")
async def login(request: Request, body: LoginRequest):
    """Authenticate user and return JWT tokens."""
    auth = get_auth_service()
    ip_address = request.client.host if request.client else ""

    result = auth.authenticate(body.username, body.password, ip_address)
    if result is None:
        audit = get_audit_store()
        audit.append(
            user_id=body.username,
            role="unknown",
            action="login_failed",
            resource_type="auth",
            ip_address=ip_address,
            success=False,
            details=f"Failed login attempt for {body.username}",
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session_mgr = get_session_manager()
    session = session_mgr.create_session(
        user_id=result["user"]["user_id"],
        role=result["user"]["role"],
        ip_address=ip_address,
    )

    audit = get_audit_store()
    audit.append(
        user_id=result["user"]["user_id"],
        role=result["user"]["role"],
        action="login_success",
        resource_type="auth",
        ip_address=ip_address,
        success=True,
    )

    return {
        **result,
        "session_id": session.session_id,
    }


@router.post("/register")
async def register(request: Request, body: RegisterRequest):
    """Register a new user account."""
    auth = get_auth_service()
    try:
        role = Role(body.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {body.role}")

    user = auth.create_user(
        username=body.username,
        password=body.password,
        role=role,
        provider_id=body.provider_id,
        organization_id=body.organization_id,
    )

    audit = get_audit_store()
    audit.append(
        user_id=user.user_id,
        role=role.value,
        action="user_registered",
        resource_type="auth",
        success=True,
        details=f"New user: {body.username}",
    )

    return {"user": user.to_dict()}


@router.post("/refresh")
async def refresh_token(body: RefreshRequest):
    """Refresh access token with rotation — returns new access + new refresh token."""
    auth = get_auth_service()
    result = auth.refresh_token(body.refresh_token)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")
    return result


@router.post("/logout")
async def logout(request: Request):
    """Invalidate the current session and revoke all refresh tokens for it."""
    session_id = getattr(request.state, "session_id", "")
    auth = get_auth_service()
    session_mgr = get_session_manager()

    if session_id:
        auth.revoke_all_session_tokens(session_id)
        session_mgr.invalidate_session(session_id)

    user_id = getattr(request.state, "user_id", "")
    audit = get_audit_store()
    audit.append(
        user_id=user_id,
        role=getattr(request.state, "user_role", ""),
        action="logout",
        resource_type="auth",
        success=True,
    )
    return {"status": "logged_out"}


class RevokeAllRequest(BaseModel):
    user_id: str


@router.post("/revoke-all")
async def revoke_all_tokens(request: Request, body: RevokeAllRequest):
    """Admin endpoint: revoke all refresh tokens for a user."""
    user_id = getattr(request.state, "user_id", "")
    role = getattr(request.state, "user_role", "")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    auth = get_auth_service()
    count = auth.revoke_all_user_tokens(body.user_id)

    audit = get_audit_store()
    audit.append(
        user_id=user_id,
        role=role,
        action="revoke_all_tokens",
        resource_type="auth",
        success=True,
        details=f"Revoked {count} tokens for user {body.user_id}",
    )
    return {"status": "revoked", "count": count}


@router.post("/emergency-access")
async def emergency_access(request: Request, body: EmergencyAccessRequest):
    """Request emergency (break-glass) access."""
    emergency = get_emergency_service()
    ip_address = request.client.host if request.client else ""

    grant = emergency.request_emergency_access(
        user_id=body.user_id,
        reason=body.reason,
        emergency_code=body.emergency_code,
        ip_address=ip_address,
    )

    if grant is None:
        audit = get_audit_store()
        audit.append(
            user_id=body.user_id,
            role="unknown",
            action="emergency_access_denied",
            resource_type="auth",
            ip_address=ip_address,
            success=False,
            details="Invalid emergency code or reason",
        )
        raise HTTPException(status_code=403, detail="Emergency access denied")

    audit = get_audit_store()
    audit.append(
        user_id=body.user_id,
        role="admin",
        action="emergency_access_granted",
        resource_type="auth",
        ip_address=ip_address,
        success=True,
        details=f"Reason: {body.reason[:200]}",
    )

    return {"grant": grant.to_dict()}


@router.post("/emergency-access/review")
async def review_emergency_access(request: Request, body: ReviewEmergencyRequest):
    """Post-access review of emergency access (required within 24 hours)."""
    user_id = getattr(request.state, "user_id", "")
    emergency = get_emergency_service()

    success = emergency.review_emergency_access(
        grant_id=body.grant_id,
        reviewer_id=user_id,
        review_notes=body.review_notes,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Grant not found")

    audit = get_audit_store()
    audit.append(
        user_id=user_id,
        role=getattr(request.state, "user_role", ""),
        action="emergency_access_reviewed",
        resource_type="auth",
        success=True,
        details=f"Grant {body.grant_id} reviewed",
    )

    return {"status": "reviewed"}


@router.get("/emergency-access/active")
async def active_emergency_grants():
    """Get all active emergency access grants."""
    emergency = get_emergency_service()
    grants = emergency.get_active_grants()
    return {"grants": [g.to_dict() for g in grants]}


@router.get("/stats")
async def auth_stats():
    """Get authentication statistics."""
    auth = get_auth_service()
    session_mgr = get_session_manager()
    emergency = get_emergency_service()

    return {
        "users": auth.get_stats(),
        "sessions": session_mgr.get_stats(),
        "emergency_access": emergency.get_stats(),
    }
