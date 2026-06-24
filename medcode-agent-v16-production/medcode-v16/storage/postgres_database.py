"""
MedCode AI Agent -- PostgreSQL Storage / Database
=================================================
PostgreSQL-compatible database for sessions, coded results, and feedback.
Uses connection pooling and PostgreSQL-native syntax.
"""

import json
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

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
from security.encryption import get_encryption


class PostgresDatabase:
    """
    PostgreSQL database manager for coding sessions, results, and feedback.
    Uses psycopg2 with ThreadedConnectionPool for thread-safe connections.
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
        """Create tables if they don't exist."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id VARCHAR(64) PRIMARY KEY,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    clinical_note TEXT,
                    note_type TEXT,
                    mode TEXT,
                    status VARCHAR(32) DEFAULT 'pending',
                    processing_time_s REAL,
                    confidence_overall REAL,
                    needs_human_review INTEGER DEFAULT 0,
                    raw_response TEXT
                );

                CREATE TABLE IF NOT EXISTS coded_results (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(64) REFERENCES sessions(id),
                    code TEXT,
                    code_name TEXT,
                    vocabulary TEXT,
                    code_type TEXT,
                    sequence_order INTEGER,
                    llm_score INTEGER,
                    is_billable INTEGER DEFAULT 0,
                    reasoning TEXT,
                    confidence_level TEXT
                );

                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(64) REFERENCES sessions(id),
                    code TEXT,
                    action TEXT,
                    corrected_code TEXT,
                    corrected_by TEXT DEFAULT 'user',
                    timestamp TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_created
                    ON sessions(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_results_session
                    ON coded_results(session_id);
                CREATE INDEX IF NOT EXISTS idx_feedback_session
                    ON feedback(session_id);
            """)

    def save_session(self, session_id: str, note: str, note_type: str,
                     mode: str, status: str = "pending") -> str:
        """Save a session record. Encrypts PHI fields before storage."""
        if not session_id:
            session_id = str(uuid.uuid4())

        enc = get_encryption()
        encrypted_note = enc.encrypt(note[:500])

        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO sessions (id, clinical_note, note_type, mode, status)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (id) DO UPDATE SET
                       clinical_note = EXCLUDED.clinical_note,
                       note_type = EXCLUDED.note_type,
                       mode = EXCLUDED.mode,
                       status = EXCLUDED.status""",
                (session_id, encrypted_note, note_type, mode, status),
            )
        return session_id

    def update_session(self, session_id: str, **kwargs):
        """Update session fields."""
        allowed = {"status", "processing_time_s", "confidence_overall",
                   "needs_human_review", "raw_response"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return

        set_clause = ", ".join(f"{k} = %s" for k in updates)
        values = list(updates.values()) + [session_id]

        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                f"UPDATE sessions SET {set_clause} WHERE id = %s",
                values,
            )

    def save_results(self, session_id: str, results: list[dict]):
        """Save coded results for a session."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            for i, r in enumerate(results):
                cur.execute(
                    """INSERT INTO coded_results
                       (session_id, code, code_name, vocabulary, code_type,
                        sequence_order, llm_score, is_billable, reasoning, confidence_level)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        session_id,
                        r.get("code", ""),
                        r.get("name", ""),
                        r.get("vocabulary", "ICD10CM"),
                        r.get("code_type", "secondary_dx"),
                        i + 1,
                        r.get("llm_score", 0),
                        1 if r.get("is_billable") else 0,
                        r.get("reasoning", ""),
                        r.get("confidence_level", "MED"),
                    ),
                )

    def save_feedback(self, session_id: str, code: str, action: str,
                      corrected_code: str = None, corrected_by: str = "user"):
        """Save user feedback on a coded result."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO feedback
                   (session_id, code, action, corrected_code, corrected_by)
                   VALUES (%s, %s, %s, %s, %s)""",
                (session_id, code, action, corrected_code, corrected_by),
            )

    def get_session(self, session_id: str, decrypt: bool = True) -> Optional[dict]:
        """Get a session by ID. Decrypts PHI fields if requested."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM sessions WHERE id = %s", (session_id,))
            row = cur.fetchone()
            if row is None:
                return None

            col_names = [desc[0] for desc in cur.description]
            session = dict(zip(col_names, row))

            if decrypt and session.get("clinical_note"):
                enc = get_encryption()
                try:
                    session["clinical_note"] = enc.decrypt(session["clinical_note"])
                except Exception:
                    pass

            cur.execute(
                "SELECT * FROM coded_results WHERE session_id = %s ORDER BY sequence_order",
                (session_id,),
            )
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]
            session["results"] = [dict(zip(col_names, r)) for r in rows]

            return session

    def get_history(self, limit: int = 20, offset: int = 0, decrypt: bool = True) -> list[dict]:
        """Get recent session history. Decrypts PHI fields if requested."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT id, created_at, clinical_note, note_type, mode, status,
                          processing_time_s, confidence_overall, needs_human_review
                   FROM sessions
                   ORDER BY created_at DESC
                   LIMIT %s OFFSET %s""",
                (limit, offset),
            )
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]
            sessions = [dict(zip(col_names, r)) for r in rows]

            if decrypt:
                enc = get_encryption()
                for s in sessions:
                    if s.get("clinical_note"):
                        try:
                            s["clinical_note"] = enc.decrypt(s["clinical_note"])
                        except Exception:
                            pass

            return sessions

    def get_stats(self) -> dict:
        """Get aggregated statistics."""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM sessions")
            total = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM sessions WHERE created_at::date = CURRENT_DATE"
            )
            today = cur.fetchone()[0]

            cur.execute(
                "SELECT AVG(confidence_overall) FROM sessions WHERE confidence_overall IS NOT NULL"
            )
            avg_confidence = cur.fetchone()[0] or 0

            return {
                "total_sessions": total,
                "today_sessions": today,
                "avg_confidence": round(avg_confidence, 1),
            }

    def close(self):
        """Close the connection pool."""
        if self._pool:
            self._pool.closeall()
