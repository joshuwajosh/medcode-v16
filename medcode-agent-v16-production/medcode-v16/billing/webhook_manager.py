"""
MedCode AI V19 — Webhook Manager
=================================
Registers webhook URLs for claim status events and delivers
POST requests with HMAC-SHA256 signatures.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from billing.webhook_models import (
    VALID_WEBHOOK_EVENTS,
    Webhook,
    WebhookDelivery,
)

DEFAULT_DB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
)

MAX_RETRIES = 3
RETRY_DELAYS = [1, 5, 25]  # seconds — exponential backoff


class WebhookManager:
    """
    Manages webhook registrations and event delivery.
    Uses the same SQLite database directory as the claim tracker.
    """

    def __init__(self, db_dir: Optional[str] = None):
        self.db_dir = db_dir or DEFAULT_DB_DIR
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, "claims.db")
        self._lock = threading.Lock()
        self._init_db()

    # ── DB Setup ────────────────────────────────────────────────────────

    def _init_db(self):
        """Create webhook tables if they don't exist."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS webhooks (
                        id TEXT PRIMARY KEY,
                        organization_id TEXT NOT NULL,
                        url TEXT NOT NULL,
                        events TEXT NOT NULL,
                        secret TEXT NOT NULL,
                        active INTEGER DEFAULT 1,
                        created_at TEXT
                    );

                    CREATE TABLE IF NOT EXISTS webhook_deliveries (
                        id TEXT PRIMARY KEY,
                        webhook_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        response_code INTEGER,
                        delivered_at TEXT,
                        FOREIGN KEY (webhook_id) REFERENCES webhooks(id)
                    );

                    CREATE INDEX IF NOT EXISTS idx_webhooks_org
                        ON webhooks(organization_id);
                    CREATE INDEX IF NOT EXISTS idx_deliveries_webhook
                        ON webhook_deliveries(webhook_id);
                    CREATE INDEX IF NOT EXISTS idx_deliveries_status
                        ON webhook_deliveries(status);
                """)
                conn.commit()
            finally:
                conn.close()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── Public API ──────────────────────────────────────────────────────

    def register_webhook(
        self,
        organization_id: str,
        url: str,
        events: List[str],
        secret: str,
    ) -> Webhook:
        """Register a new webhook endpoint for an organization."""
        for ev in events:
            if ev not in VALID_WEBHOOK_EVENTS:
                raise ValueError(
                    f"Invalid event type '{ev}'. "
                    f"Valid events: {VALID_WEBHOOK_EVENTS}"
                )

        webhook_id = f"wh_{uuid.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc).isoformat()
        events_json = json.dumps(events)

        webhook = Webhook(
            id=webhook_id,
            organization_id=organization_id,
            url=url,
            events=events,
            secret=secret,
            active=True,
            created_at=now,
        )

        conn = self._conn()
        try:
            conn.execute(
                """INSERT INTO webhooks
                   (id, organization_id, url, events, secret, active, created_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?)""",
                (webhook_id, organization_id, url, events_json, secret, now),
            )
            conn.commit()
        finally:
            conn.close()

        return webhook

    def unregister_webhook(self, webhook_id: str) -> bool:
        """Deactivate a webhook. Returns True if found and deactivated."""
        conn = self._conn()
        try:
            cur = conn.execute(
                "SELECT id FROM webhooks WHERE id = ?", (webhook_id,)
            )
            if not cur.fetchone():
                return False
            conn.execute(
                "UPDATE webhooks SET active = 0 WHERE id = ?", (webhook_id,)
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def list_webhooks(self, organization_id: str) -> List[Webhook]:
        """List all active webhooks for an organization."""
        conn = self._conn()
        try:
            rows = conn.execute(
                """SELECT * FROM webhooks
                   WHERE organization_id = ? AND active = 1
                   ORDER BY created_at DESC""",
                (organization_id,),
            ).fetchall()
            return [self._row_to_webhook(r) for r in rows]
        finally:
            conn.close()

    def trigger_event(self, event_type: str, payload: dict) -> None:
        """
        Fire all matching webhooks for the given event type.
        Delivery is non-blocking: a background thread handles retries.
        """
        if event_type not in VALID_WEBHOOK_EVENTS:
            return

        organization_id = payload.get("organization_id", "")
        conn = self._conn()
        try:
            rows = conn.execute(
                """SELECT * FROM webhooks
                   WHERE active = 1 AND organization_id = ?""",
                (organization_id,),
            ).fetchall()
        finally:
            conn.close()

        for row in rows:
            webhook = self._row_to_webhook(row)
            if event_type not in webhook.events:
                continue
            thread = threading.Thread(
                target=self._deliver_with_retries,
                args=(webhook, event_type, payload),
                daemon=True,
            )
            thread.start()

    def verify_signature(
        self, payload: bytes, signature: str, secret: str
    ) -> bool:
        """Verify HMAC-SHA256 signature of a webhook payload."""
        expected = hmac.new(
            secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def get_deliveries(
        self, webhook_id: str, limit: int = 50
    ) -> List[WebhookDelivery]:
        """Return recent delivery records for a webhook."""
        conn = self._conn()
        try:
            rows = conn.execute(
                """SELECT * FROM webhook_deliveries
                   WHERE webhook_id = ?
                   ORDER BY delivered_at DESC
                   LIMIT ?""",
                (webhook_id, limit),
            ).fetchall()
            return [
                WebhookDelivery(
                    id=r["id"],
                    webhook_id=r["webhook_id"],
                    event_type=r["event_type"],
                    status=r["status"],
                    response_code=r["response_code"],
                    delivered_at=r["delivered_at"],
                )
                for r in rows
            ]
        finally:
            conn.close()

    # ── Internal Delivery ───────────────────────────────────────────────

    def _deliver_with_retries(
        self,
        webhook: Webhook,
        event_type: str,
        payload: dict,
    ):
        """Attempt delivery up to MAX_RETRIES times with backoff."""
        import urllib.request
        import urllib.error

        delivery_id = f"dlv_{uuid.uuid4().hex[:12]}"
        body = json.dumps({
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        }).encode("utf-8")

        signature = hmac.new(
            webhook.secret.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-ID": webhook.id,
            "X-Event-Type": event_type,
        }

        last_error = ""
        response_code = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                req = urllib.request.Request(
                    webhook.url,
                    data=body,
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    response_code = resp.getcode()
                    if 200 <= response_code < 300:
                        self._record_delivery(
                            delivery_id, webhook.id, event_type,
                            "sent", response_code,
                        )
                        return
                    last_error = f"HTTP {response_code}"
            except (urllib.error.URLError, urllib.error.HTTPError) as exc:
                last_error = str(exc)
                if hasattr(exc, "code"):
                    response_code = exc.code
            except Exception as exc:
                last_error = str(exc)

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAYS[attempt - 1])

        self._record_delivery(
            delivery_id, webhook.id, event_type,
            "failed", response_code,
        )

    def _record_delivery(
        self,
        delivery_id: str,
        webhook_id: str,
        event_type: str,
        status: str,
        response_code: Optional[int],
    ):
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        try:
            conn.execute(
                """INSERT INTO webhook_deliveries
                   (id, webhook_id, event_type, status, response_code, delivered_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (delivery_id, webhook_id, event_type, status, response_code, now),
            )
            conn.commit()
        finally:
            conn.close()

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_webhook(row: sqlite3.Row) -> Webhook:
        import json as _json
        events_raw = row["events"]
        events = _json.loads(events_raw) if isinstance(events_raw, str) else events_raw
        return Webhook(
            id=row["id"],
            organization_id=row["organization_id"],
            url=row["url"],
            events=events,
            secret=row["secret"],
            active=bool(row["active"]),
            created_at=row["created_at"],
        )
