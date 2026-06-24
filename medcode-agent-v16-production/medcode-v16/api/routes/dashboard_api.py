"""
MedCode AI V19 — Dashboard API Routes
=======================================
Aggregated stats, activity feed, and chart data for the admin dashboard.
"""
from __future__ import annotations

import os
import time
from typing import Optional

from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/v19/dashboard", tags=["dashboard"])

_start_time = time.time()


@router.get("/stats")
async def dashboard_stats():
    """Aggregate dashboard summary statistics."""
    total_claims = 0
    pending_claims = 0
    paid_claims = 0
    denied_claims = 0
    total_revenue = 0.0

    try:
        from billing.claim_tracker import ClaimTracker
        tracker = ClaimTracker()
        all_claims = tracker.list_claims(limit=5000)
        total_claims = len(all_claims)
        for c in all_claims:
            s = (c.get("status") or "").lower()
            if s == "paid":
                paid_claims += 1
            elif s == "pending":
                pending_claims += 1
            elif s == "denied":
                denied_claims += 1
            total_revenue += c.get("total_charges", 0) or 0
    except Exception:
        pass

    db_status = "Connected"
    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "medcode.db",
        )
        if not os.path.isfile(db_path):
            db_status = "File-based (no DB)"
    except Exception:
        db_status = "Unknown"

    uptime_s = int(time.time() - _start_time)
    hours = uptime_s // 3600
    mins = (uptime_s % 3600) // 60
    uptime_str = f"{hours}h {mins}m" if hours else f"{mins}m"

    return {
        "total_claims": total_claims,
        "pending_claims": pending_claims,
        "paid_claims": paid_claims,
        "denied_claims": denied_claims,
        "total_revenue": round(total_revenue, 2),
        "version": "19.0.0-hipaa",
        "db_status": db_status,
        "uptime": uptime_str,
    }


@router.get("/activity")
async def dashboard_activity(limit: int = Query(default=10, ge=1, le=100)):
    """Recent activity feed from audit log and claim history."""
    events = []

    try:
        from audit.security_events import SecurityEventRegistry
        registry = SecurityEventRegistry()
        raw = registry.get_events(limit=limit) if hasattr(registry, "get_events") else []
        for ev in raw:
            events.append({
                "type": ev.get("action", "unknown"),
                "description": ev.get("details") or ev.get("action", "Event"),
                "timestamp": ev.get("timestamp", ""),
            })
    except Exception:
        pass

    try:
        from billing.claim_tracker import ClaimTracker
        tracker = ClaimTracker()
        recent = tracker.list_claims(limit=limit)
        for c in recent:
            events.append({
                "type": c.get("status", "updated"),
                "description": f"Claim {c.get('claim_id', '—')} → {c.get('status', 'updated')}",
                "timestamp": c.get("created_at", c.get("updated_at", "")),
            })
    except Exception:
        pass

    events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return {"events": events[:limit]}


@router.get("/charts")
async def dashboard_charts():
    """Chart data: claims by status and revenue trend (last 30 days)."""
    by_status = {}
    daily_revenue = {}

    try:
        from billing.claim_tracker import ClaimTracker
        tracker = ClaimTracker()
        claims = tracker.list_claims(limit=5000)

        for c in claims:
            s = c.get("status", "unknown")
            by_status[s] = by_status.get(s, 0) + 1

            created = c.get("created_at", "")
            if created:
                day = created[:10]
                daily_revenue[day] = daily_revenue.get(day, 0) + (c.get("total_charges", 0) or 0)
    except Exception:
        pass

    from datetime import datetime, timedelta

    today = datetime.utcnow().date()
    trend = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.isoformat()
        trend.append({"date": day_str, "revenue": round(daily_revenue.get(day_str, 0), 2)})

    return {
        "by_status": by_status,
        "revenue_trend": trend,
    }
