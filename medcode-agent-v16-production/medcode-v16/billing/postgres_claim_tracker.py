"""
MedCode AI -- PostgreSQL Claim Lifecycle Tracking
=================================================
PostgreSQL-based claim database for tracking claim status
through the complete revenue cycle.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.config import (
    DATABASE_URL,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_SSL_MODE,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
)


# Valid claim status transitions
STATUS_TRANSITIONS = {
    "draft": ["validated"],
    "validated": ["submitted", "draft"],
    "submitted": ["acknowledged", "denied"],
    "acknowledged": ["paid", "denied", "pending_review"],
    "pending_review": ["paid", "denied", "appealed"],
    "denied": ["appealed", "resubmitted"],
    "appealed": ["paid", "denied"],
    "resubmitted": ["acknowledged", "denied"],
    "paid": [],
}


class PostgresClaimTracker:
    """
    PostgreSQL-based claim lifecycle tracker.
    Manages claim status, history, and notes.
    """

    def __init__(self, pool_size: int = None, max_overflow: int = None):
        self._pool = None
        self._pool_size = pool_size or DB_POOL_SIZE
        self._max_overflow = max_overflow or DB_MAX_OVERFLOW
        self._init_pool()
        self._init_db()

    def _build_dsn(self) -> str:
        """Build DSN from individual config vars or DATABASE_URL."""
        if DATABASE_URL and DATABASE_URL.startswith("postgresql"):
            return DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")
        return (
            f"host={POSTGRES_HOST} "
            f"port={POSTGRES_PORT} "
            f"dbname={POSTGRES_DB} "
            f"user={POSTGRES_USER} "
            f"password={POSTGRES_PASSWORD}"
        )

    def _init_pool(self):
        """Initialize connection pool."""
        try:
            from psycopg2.pool import ThreadedConnectionPool
        except ImportError:
            raise ImportError(
                "psycopg2 is required for PostgreSQL support. "
                "Install with: pip install psycopg2-binary"
            )

        dsn = self._build_dsn()
        sslmode = POSTGRES_SSL_MODE
        ssl_kwargs = {}
        if sslmode and sslmode != "disable":
            ssl_kwargs["sslmode"] = sslmode

        self._pool = ThreadedConnectionPool(
            1,
            self._pool_size,
            dsn,
            **ssl_kwargs,
        )

    @contextmanager
    def _get_conn(self):
        """Context manager that yields a connection and handles commit/rollback."""
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def _init_db(self):
        """Initialize the PostgreSQL database schema."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS claims (
                    claim_id VARCHAR(64) PRIMARY KEY,
                    organization_id TEXT DEFAULT '',
                    patient_name TEXT,
                    payer_name TEXT,
                    provider_npi TEXT,
                    total_charges REAL DEFAULT 0.0,
                    status VARCHAR(32) DEFAULT 'draft',
                    claim_type VARCHAR(32) DEFAULT 'professional',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS claim_status_history (
                    id SERIAL PRIMARY KEY,
                    claim_id VARCHAR(64) NOT NULL REFERENCES claims(claim_id),
                    old_status VARCHAR(32),
                    new_status VARCHAR(32) NOT NULL,
                    notes TEXT,
                    timestamp TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS claim_notes (
                    id SERIAL PRIMARY KEY,
                    claim_id VARCHAR(64) NOT NULL REFERENCES claims(claim_id),
                    note_type VARCHAR(32) DEFAULT 'general',
                    content TEXT,
                    created_by VARCHAR(64) DEFAULT 'system',
                    timestamp TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
                CREATE INDEX IF NOT EXISTS idx_claims_payer ON claims(payer_name);
                CREATE INDEX IF NOT EXISTS idx_claims_updated ON claims(updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_history_claim ON claim_status_history(claim_id);
                CREATE INDEX IF NOT EXISTS idx_notes_claim ON claim_notes(claim_id);
            """)

    def submit(
        self,
        claim_id: str,
        patient_name: str = "",
        payer_name: str = "",
        provider_npi: str = "",
        total_charges: float = 0.0,
        claim_type: str = "professional",
        organization_id: str = "",
    ) -> Dict[str, Any]:
        """
        Submit a new claim for tracking.
        Returns:
            Dict with claim_id and status.
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO claims
                (claim_id, organization_id, patient_name, payer_name, provider_npi,
                 total_charges, status, claim_type, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, 'draft', %s, %s, %s)
                ON CONFLICT (claim_id) DO UPDATE SET
                    organization_id = EXCLUDED.organization_id,
                    patient_name = EXCLUDED.patient_name,
                    payer_name = EXCLUDED.payer_name,
                    provider_npi = EXCLUDED.provider_npi,
                    total_charges = EXCLUDED.total_charges,
                    status = 'draft',
                    claim_type = EXCLUDED.claim_type,
                    updated_at = EXCLUDED.updated_at
                """,
                (claim_id, organization_id, patient_name, payer_name, provider_npi,
                 total_charges, claim_type, now, now),
            )
            cur.execute(
                """
                INSERT INTO claim_status_history
                (claim_id, old_status, new_status, notes, timestamp)
                VALUES (%s, NULL, 'draft', 'Claim created', %s)
                """,
                (claim_id, now),
            )
        return {"claim_id": claim_id, "status": "draft", "created_at": now}

    def update_status(
        self,
        claim_id: str,
        new_status: str,
        notes: str = "",
        organization_id: str = "",
    ) -> Dict[str, Any]:
        """
        Update claim status with validation of allowed transitions.
        Returns:
            Dict with claim_id, old_status, new_status, and error if any.
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT status FROM claims WHERE claim_id = %s",
                (claim_id,),
            )
            row = cur.fetchone()

            if not row:
                return {"error": f"Claim {claim_id} not found"}

            old_status = row[0]

            if new_status not in STATUS_TRANSITIONS.get(old_status, []):
                return {
                    "error": (
                        f"Invalid transition: {old_status} -> {new_status}. "
                        f"Allowed: {STATUS_TRANSITIONS.get(old_status, [])}"
                    ),
                    "claim_id": claim_id,
                    "current_status": old_status,
                }

            cur.execute(
                "UPDATE claims SET status = %s, updated_at = %s WHERE claim_id = %s",
                (new_status, now, claim_id),
            )
            cur.execute(
                """
                INSERT INTO claim_status_history
                (claim_id, old_status, new_status, notes, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (claim_id, old_status, new_status, notes, now),
            )
        self._trigger_webhook(new_status, {
            "claim_id": claim_id,
            "old_status": old_status,
            "new_status": new_status,
            "organization_id": organization_id or "",
            "updated_at": now,
        })
        return {
            "claim_id": claim_id,
            "old_status": old_status,
            "new_status": new_status,
            "updated_at": now,
        }

    def get_status(self, claim_id: str) -> Dict[str, Any]:
        """
        Get current claim status.
        Returns:
            Dict with claim details or error.
        """
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM claims WHERE claim_id = %s", (claim_id,))
            row = cur.fetchone()

            if not row:
                return {"error": f"Claim {claim_id} not found"}

            col_names = [desc[0] for desc in cur.description]
            return dict(zip(col_names, row))

    def get_history(self, claim_id: str) -> List[Dict[str, Any]]:
        """
        Get complete status history for a claim.
        Returns:
            List of status change records.
        """
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM claim_status_history
                WHERE claim_id = %s
                ORDER BY timestamp ASC
                """,
                (claim_id,),
            )
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]
            return [dict(zip(col_names, r)) for r in rows]

    def add_note(
        self,
        claim_id: str,
        content: str,
        note_type: str = "general",
        created_by: str = "system",
    ) -> Dict[str, Any]:
        """Add a note to a claim."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO claim_notes
                (claim_id, note_type, content, created_by, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (claim_id, note_type, content, created_by, now),
            )
        return {"claim_id": claim_id, "note_type": note_type, "timestamp": now}

    def get_notes(self, claim_id: str) -> List[Dict[str, Any]]:
        """Get all notes for a claim."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM claim_notes
                WHERE claim_id = %s
                ORDER BY timestamp DESC
                """,
                (claim_id,),
            )
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]
            return [dict(zip(col_names, r)) for r in rows]

    def list_claims(
        self,
        status: Optional[str] = None,
        payer_name: Optional[str] = None,
        organization_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List claims with optional filters."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            query = "SELECT * FROM claims WHERE 1=1"
            params = []

            if organization_id:
                query += " AND organization_id = %s"
                params.append(organization_id)
            if status:
                query += " AND status = %s"
                params.append(status)
            if payer_name:
                query += " AND payer_name = %s"
                params.append(payer_name)

            query += " ORDER BY updated_at DESC LIMIT %s"
            params.append(limit)

            cur.execute(query, params)
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]
            return [dict(zip(col_names, r)) for r in rows]

    def get_claim_count(self) -> Dict[str, int]:
        """Get claim counts by status."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT status, COUNT(*) FROM claims GROUP BY status")
            rows = cur.fetchall()
            return {row[0]: row[1] for row in rows}

    def _trigger_webhook(self, new_status: str, payload: dict):
        """Trigger webhook event for claim status changes."""
        event_map = {
            "submitted": "claim.submitted",
            "acknowledged": "claim.acknowledged",
            "paid": "claim.paid",
            "denied": "claim.denied",
            "appealed": "claim.appealed",
        }
        event_type = event_map.get(new_status)
        if not event_type:
            return
        try:
            from billing.webhook_manager import WebhookManager
            manager = WebhookManager()
            manager.trigger_event(event_type, payload)
        except Exception:
            pass

    def close(self):
        """Close the connection pool."""
        if self._pool:
            self._pool.closeall()
