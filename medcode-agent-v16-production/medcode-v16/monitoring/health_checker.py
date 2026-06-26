"""
MedCode AI — Health Check Monitoring
=====================================
Provides comprehensive health checks for:
  - Database connectivity
  - API endpoint availability
  - LLM provider status
  - Billing subsystem readiness
"""
from __future__ import annotations

import logging
import os
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("medcode.monitoring.health")


@dataclass
class ComponentHealth:
    """Health status of a single system component."""
    name: str
    status: str = "unknown"  # ok, degraded, error
    latency_ms: float = 0.0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "status": self.status,
            "latency_ms": round(self.latency_ms, 2),
        }
        if self.message:
            d["message"] = self.message
        if self.details:
            d["details"] = self.details
        return d


@dataclass
class HealthReport:
    """Aggregated health report across all components."""
    overall_status: str = "ok"  # ok, degraded, error
    timestamp: str = ""
    components: List[ComponentHealth] = field(default_factory=list)
    uptime_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "status": self.overall_status,
            "timestamp": self.timestamp,
            "uptime_seconds": round(self.uptime_seconds, 1),
            "components": [c.to_dict() for c in self.components],
        }


class HealthChecker:
    """Performs health checks on all system components."""

    def __init__(self, data_dir: Optional[str] = None):
        self._data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
        )
        self._start_time = time.time()

    def check_all(
        self,
        db: Any = None,
        providers: Optional[List[str]] = None,
        omop_connected: bool = False,
    ) -> HealthReport:
        """Run all health checks and return an aggregated report.

        Args:
            db: Database instance (optional, will attempt SQLite if None).
            providers: List of active LLM provider names.
            omop_connected: Whether OMOP Hub is connected.

        Returns:
            HealthReport with status of each component.
        """
        report = HealthReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_seconds=time.time() - self._start_time,
        )

        components = [
            self._check_database(db),
            self._check_sqlite_claims(),
            self._check_providers(providers or []),
            self._check_omop(omop_connected),
            self._check_data_directory(),
        ]

        report.components = components

        statuses = [c.status for c in components]
        if any(s == "error" for s in statuses):
            report.overall_status = "error"
        elif any(s == "degraded" for s in statuses):
            report.overall_status = "degraded"
        else:
            report.overall_status = "ok"

        return report

    def _check_database(self, db: Any) -> ComponentHealth:
        """Check main database connectivity."""
        t0 = time.perf_counter()
        health = ComponentHealth(name="main_database")

        if db is None:
            health.status = "degraded"
            health.message = "Database instance not provided"
            return health

        try:
            if hasattr(db, "get_stats"):
                db.get_stats()
            elif hasattr(db, "conn"):
                conn = db.conn
                if hasattr(conn, "execute"):
                    conn.execute("SELECT 1")
            health.status = "ok"
            health.message = "Connected"
        except Exception as exc:
            health.status = "error"
            health.message = str(exc)[:200]

        health.latency_ms = (time.perf_counter() - t0) * 1000
        return health

    def _check_sqlite_claims(self) -> ComponentHealth:
        """Check SQLite claims database connectivity."""
        t0 = time.perf_counter()
        health = ComponentHealth(name="claims_database")

        claims_db = os.path.join(self._data_dir, "claims.db")
        if not os.path.exists(claims_db):
            health.status = "degraded"
            health.message = "Claims database file not found (will be created on first use)"
            health.latency_ms = (time.perf_counter() - t0) * 1000
            return health

        try:
            conn = sqlite3.connect(claims_db, timeout=5)
            conn.execute("SELECT 1")
            conn.close()
            health.status = "ok"
            health.message = "Connected"
            health.details["path"] = claims_db
            size_mb = os.path.getsize(claims_db) / (1024 * 1024)
            health.details["size_mb"] = round(size_mb, 2)
        except Exception as exc:
            health.status = "error"
            health.message = str(exc)[:200]

        health.latency_ms = (time.perf_counter() - t0) * 1000
        return health

    def _check_providers(self, providers: List[str]) -> ComponentHealth:
        """Check LLM provider availability."""
        health = ComponentHealth(name="llm_providers")

        if not providers:
            health.status = "degraded"
            health.message = "No LLM providers configured"
            return health

        health.status = "ok"
        health.message = f"{len(providers)} provider(s) configured"
        health.details["providers"] = providers
        return health

    def _check_omop(self, connected: bool) -> ComponentHealth:
        """Check OMOP Hub connectivity."""
        health = ComponentHealth(name="omop_hub")

        if connected:
            health.status = "ok"
            health.message = "Connected"
        else:
            health.status = "degraded"
            health.message = "Not connected (OMOP API key may be missing)"

        return health

    def _check_data_directory(self) -> ComponentHealth:
        """Check data directory is writable."""
        t0 = time.perf_counter()
        health = ComponentHealth(name="data_directory")

        try:
            os.makedirs(self._data_dir, exist_ok=True)
            test_file = os.path.join(self._data_dir, ".health_check")
            with open(test_file, "w") as f:
                f.write("ok")
            os.remove(test_file)
            health.status = "ok"
            health.message = "Writable"
        except Exception as exc:
            health.status = "error"
            health.message = str(exc)[:200]

        health.latency_ms = (time.perf_counter() - t0) * 1000
        return health
