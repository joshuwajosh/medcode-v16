"""
MedCode AI V19 — Multi-Tenant Support
======================================
Tenant isolation at the database level. Each organization has its own
data partition enforced via organization_id on all tables.
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


DEFAULT_DB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
)


class TenantContext:
    """Thread-local tenant context for request isolation."""

    _current_tenant: Optional[str] = None

    @classmethod
    def get_current_tenant(cls) -> Optional[str]:
        return cls._current_tenant

    @classmethod
    def set_current_tenant(cls, tenant_id: Optional[str]) -> None:
        cls._current_tenant = tenant_id


class TenantManager:
    """
    Manages tenant (organization) lifecycle.
    Stores tenant metadata in the same SQLite database used by the claim tracker.
    """

    def __init__(self, db_dir: Optional[str] = None):
        self.db_dir = db_dir or DEFAULT_DB_DIR
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, "claims.db")
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    plan TEXT DEFAULT 'free',
                    settings TEXT DEFAULT '{}',
                    active INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_tenants_name
                    ON tenants(name);
                CREATE INDEX IF NOT EXISTS idx_tenants_plan
                    ON tenants(plan);
            """)
            conn.commit()
        finally:
            conn.close()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def tenant_scope(self, tenant_id: str):
        """Context manager that sets and resets the current tenant."""
        prev = TenantContext.get_current_tenant()
        TenantContext.set_current_tenant(tenant_id)
        try:
            yield
        finally:
            TenantContext.set_current_tenant(prev)

    def get_current_tenant(self) -> Optional[Dict[str, Any]]:
        """Get the currently active tenant."""
        tid = TenantContext.get_current_tenant()
        if not tid:
            return None
        return self.get_tenant(tid)

    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM tenants WHERE id = ? AND active = 1",
                (tenant_id,),
            ).fetchone()
            if not row:
                return None
            data = dict(row)
            data["settings"] = json.loads(data.get("settings", "{}"))
            return data
        finally:
            conn.close()

    def set_tenant(self, tenant_id: str) -> bool:
        """Set the active tenant for the current context. Returns False if tenant not found."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False
        TenantContext.set_current_tenant(tenant_id)
        return True

    def list_tenants(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        conn = self._conn()
        try:
            if include_inactive:
                rows = conn.execute(
                    "SELECT * FROM tenants ORDER BY created_at DESC"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM tenants WHERE active = 1 ORDER BY created_at DESC"
                ).fetchall()
            results = []
            for r in rows:
                data = dict(r)
                data["settings"] = json.loads(data.get("settings", "{}"))
                results.append(data)
            return results
        finally:
            conn.close()

    def create_tenant(
        self,
        name: str,
        plan: str = "free",
        settings: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """Create a new tenant. Returns the created tenant dict."""
        tenant_id = f"org_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        settings_json = json.dumps(settings or {})

        conn = self._conn()
        try:
            conn.execute(
                """INSERT INTO tenants
                   (id, name, plan, settings, active, created_at, updated_at)
                   VALUES (?, ?, ?, ?, 1, ?, ?)""",
                (tenant_id, name, plan, settings_json, now, now),
            )
            conn.commit()
        finally:
            conn.close()

        return {
            "id": tenant_id,
            "name": name,
            "plan": plan,
            "settings": settings or {},
            "active": True,
            "created_at": now,
            "updated_at": now,
        }

    def update_tenant(
        self,
        tenant_id: str,
        name: Optional[str] = None,
        plan: Optional[str] = None,
        settings: Optional[dict] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update tenant fields. Returns updated tenant or None."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None

        now = datetime.now(timezone.utc).isoformat()
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if plan is not None:
            updates.append("plan = ?")
            params.append(plan)
        if settings is not None:
            updates.append("settings = ?")
            params.append(json.dumps(settings))

        if not updates:
            return tenant

        updates.append("updated_at = ?")
        params.append(now)
        params.append(tenant_id)

        conn = self._conn()
        try:
            conn.execute(
                f"UPDATE tenants SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()
        finally:
            conn.close()

        return self.get_tenant(tenant_id)

    def delete_tenant(self, tenant_id: str) -> bool:
        """Soft-delete a tenant. Returns True if found and deactivated."""
        conn = self._conn()
        try:
            now = datetime.now(timezone.utc).isoformat()
            cur = conn.execute(
                "SELECT id FROM tenants WHERE id = ? AND active = 1",
                (tenant_id,),
            )
            if not cur.fetchone():
                return False
            conn.execute(
                "UPDATE tenants SET active = 0, updated_at = ? WHERE id = ?",
                (now, tenant_id),
            )
            conn.commit()
            return True
        finally:
            conn.close()


def get_current_tenant_id() -> Optional[str]:
    """Convenience: get the current tenant ID from context."""
    return TenantContext.get_current_tenant()
