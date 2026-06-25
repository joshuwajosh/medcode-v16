"""
MedCode AI â€” Claim Lifecycle Tracking
======================================
SQLite-based claim database for tracking claim status
through the complete revenue cycle.
"""
from __future__ import annotations
import os
import sqlite3
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from billing.webhook_models import VALID_WEBHOOK_EVENTS


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

DEFAULT_DB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
)


class ClaimTracker:
    """
    SQLite-based claim lifecycle tracker.
    Manages claim status, history, and notes.
    """

    def __init__(self, db_dir: Optional[str] = None):
        self.db_dir = db_dir or DEFAULT_DB_DIR
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, "claims.db")
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS claims (
                    claim_id TEXT PRIMARY KEY,
                    organization_id TEXT DEFAULT '',
                    patient_name TEXT,
                    payer_name TEXT,
                    provider_npi TEXT,
                    total_charges REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'draft',
                    claim_type TEXT DEFAULT 'professional',
                    created_at TEXT,
                    updated_at TEXT
                );

                CREATE TABLE IF NOT EXISTS claim_status_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim_id TEXT NOT NULL,
                    old_status TEXT,
                    new_status TEXT NOT NULL,
                    notes TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS claim_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim_id TEXT NOT NULL,
                    note_type TEXT DEFAULT 'general',
                    content TEXT,
                    created_by TEXT DEFAULT 'system',
                    timestamp TEXT,
                    FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE
                );
            """)
            conn.commit()
        finally:
            conn.close()

    def _conn(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

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
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO claims
                (claim_id, organization_id, patient_name, payer_name, provider_npi,
                 total_charges, status, claim_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?)
                """,
                (claim_id, organization_id, patient_name, payer_name, provider_npi,
                 total_charges, claim_type, now, now),
            )
            conn.execute(
                """
                INSERT INTO claim_status_history
                (claim_id, old_status, new_status, notes, timestamp)
                VALUES (?, NULL, 'draft', 'Claim created', ?)
                """,
                (claim_id, now),
            )
            conn.commit()
        finally:
            conn.close()

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
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT status FROM claims WHERE claim_id = ?",
                (claim_id,),
            ).fetchone()

            if not row:
                return {"error": f"Claim {claim_id} not found"}

            old_status = row["status"]

            if new_status not in STATUS_TRANSITIONS.get(old_status, []):
                return {
                    "error": (
                        f"Invalid transition: {old_status} -> {new_status}. "
                        f"Allowed: {STATUS_TRANSITIONS.get(old_status, [])}"
                    ),
                    "claim_id": claim_id,
                    "current_status": old_status,
                }

            conn.execute(
                "UPDATE claims SET status = ?, updated_at = ? WHERE claim_id = ?",
                (new_status, now, claim_id),
            )
            conn.execute(
                """
                INSERT INTO claim_status_history
                (claim_id, old_status, new_status, notes, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (claim_id, old_status, new_status, notes, now),
            )
            conn.commit()
        finally:
            conn.close()

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
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM claims WHERE claim_id = ?",
                (claim_id,),
            ).fetchone()

            if not row:
                return {"error": f"Claim {claim_id} not found"}

            return dict(row)
        finally:
            conn.close()

    def get_history(self, claim_id: str) -> List[Dict[str, Any]]:
        """
        Get complete status history for a claim.

        Returns:
            List of status change records.
        """
        conn = self._conn()
        try:
            rows = conn.execute(
                """
                SELECT * FROM claim_status_history
                WHERE claim_id = ?
                ORDER BY timestamp ASC
                """,
                (claim_id,),
            ).fetchall()

            return [dict(row) for row in rows]
        finally:
            conn.close()

    def add_note(
        self,
        claim_id: str,
        content: str,
        note_type: str = "general",
        created_by: str = "system",
    ) -> Dict[str, Any]:
        """Add a note to a claim."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT INTO claim_notes
                (claim_id, note_type, content, created_by, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (claim_id, note_type, content, created_by, now),
            )
            conn.commit()
        finally:
            conn.close()

        return {"claim_id": claim_id, "note_type": note_type, "timestamp": now}

    def get_notes(self, claim_id: str) -> List[Dict[str, Any]]:
        """Get all notes for a claim."""
        conn = self._conn()
        try:
            rows = conn.execute(
                """
                SELECT * FROM claim_notes
                WHERE claim_id = ?
                ORDER BY timestamp DESC
                """,
                (claim_id,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def list_claims(
        self,
        status: Optional[str] = None,
        payer_name: Optional[str] = None,
        organization_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List claims with optional filters."""
        conn = self._conn()
        try:
            query = "SELECT * FROM claims WHERE 1=1"
            params = []

            if organization_id:
                query += " AND organization_id = ?"
                params.append(organization_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            if payer_name:
                query += " AND payer_name = ?"
                params.append(payer_name)

            query += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

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
            manager = WebhookManager(db_dir=self.db_dir)
            manager.trigger_event(event_type, payload)
        except Exception:
            pass

    def get_claim_count(self) -> Dict[str, int]:
        """Get claim counts by status."""
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT status, COUNT(*) as count FROM claims GROUP BY status"
            ).fetchall()
            return {row["status"]: row["count"] for row in rows}
        finally:
            conn.close()


def get_claim_tracker():
    """Backward-compatible factory. Returns PostgresClaimTracker if DATABASE_URL is postgresql."""
    from core.config import DATABASE_URL
    if DATABASE_URL.startswith("postgresql"):
        from billing.postgres_claim_tracker import PostgresClaimTracker
        return PostgresClaimTracker()
    return ClaimTracker()

