"""
MedCode AI V19 — Compliance API Routes
========================================
HIPAA compliance reporting and audit endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from compliance.hipaa_report import generate_hipaa_report
from security.audit_store import get_audit_store
from security.auth import get_auth_service
from security.emergency_access import get_emergency_service
from monitoring.security_monitor import get_security_monitor

router = APIRouter(prefix="/api/v19/compliance", tags=["compliance"])


@router.get("/hipaa-report")
async def hipaa_report():
    """Generate a HIPAA compliance report."""
    report = generate_hipaa_report()
    return report.to_dict()


@router.get("/audit-summary")
async def audit_summary(days: int = Query(default=30, ge=1, le=365)):
    """Get audit summary for the specified period."""
    audit = get_audit_store()
    stats = audit.get_stats()
    
    return {
        "period_days": days,
        "audit_log": stats,
        "security_monitor": get_security_monitor().get_stats(),
        "emergency_access": get_emergency_service().get_stats(),
    }


@router.get("/access-matrix")
async def access_matrix(limit: int = Query(default=100, ge=1, le=1000)):
    """Get access matrix showing who accessed what."""
    audit = get_audit_store()
    entries = audit.get_recent(limit)
    
    user_actions = {}
    for entry in entries:
        user = entry.get("user_id", "unknown")
        action = entry.get("action", "unknown")
        if user not in user_actions:
            user_actions[user] = {}
        user_actions[user][action] = user_actions[user].get(action, 0) + 1
    
    return {
        "access_matrix": user_actions,
        "total_entries": len(entries),
    }


@router.get("/phi-access-log")
async def phi_access_log(limit: int = Query(default=50, ge=1, le=500)):
    """Get log of all PHI access events."""
    audit = get_audit_store()
    entries = audit.get_phi_access_log(limit)
    return {"entries": entries, "count": len(entries)}


@router.get("/failed-access")
async def failed_access(limit: int = Query(default=50, ge=1, le=500)):
    """Get log of all failed access attempts."""
    audit = get_audit_store()
    entries = audit.get_failed_access(limit)
    return {"entries": entries, "count": len(entries)}


@router.get("/security-alerts")
async def security_alerts(
    severity: str = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Get security alerts."""
    monitor = get_security_monitor()
    alerts = monitor.get_alerts(severity=severity, limit=limit)
    return {
        "alerts": [a.to_dict() for a in alerts],
        "count": len(alerts),
        "has_critical": monitor.has_critical_alerts(),
    }


@router.get("/users")
async def list_users():
    """List all users (admin only)."""
    auth = get_auth_service()
    return {"users": auth.list_users()}


@router.get("/stats")
async def compliance_stats():
    """Get overall compliance statistics."""
    return {
        "audit": get_audit_store().get_stats(),
        "auth": get_auth_service().get_stats(),
        "security": get_security_monitor().get_stats(),
        "emergency_access": get_emergency_service().get_stats(),
    }


@router.post("/audit/verify")
async def verify_audit_chain():
    """Verify the integrity of the audit log chain."""
    audit = get_audit_store()
    result = audit.verify_chain()
    return result
