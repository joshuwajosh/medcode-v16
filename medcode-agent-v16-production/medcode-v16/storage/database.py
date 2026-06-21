"""
MedCode AI Agent -- Storage / Database
========================================
SQLite database for sessions, coded results, and feedback.
V19: PHI fields encrypted at rest using Fernet (AES-128-CBC).
HIPAA §164.312(a)(2)(iv) — Encryption and Decryption of ePHI.
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.config import DATABASE_URL
from security.encryption import get_encryption, PHI_FIELDS


class Database:
    """
    SQLite database manager for coding sessions, results, and feedback.
    Thread-safe with connection-per-operation pattern.
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            # Extract path from sqlite:/// prefix
            db_url = DATABASE_URL
            if db_url.startswith("sqlite:///"):
                db_path = db_url[len("sqlite:///"):]
            else:
                db_path = "medcode.db"
        
        self.db_path = Path(db_path)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get a new connection (thread-safe)."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    clinical_note TEXT,
                    note_type TEXT,
                    mode TEXT,
                    status TEXT DEFAULT 'pending',
                    processing_time_s REAL,
                    confidence_overall REAL,
                    needs_human_review INTEGER DEFAULT 0,
                    raw_response TEXT
                );

                CREATE TABLE IF NOT EXISTS coded_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT REFERENCES sessions(id),
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
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT REFERENCES sessions(id),
                    code TEXT,
                    action TEXT,
                    corrected_code TEXT,
                    corrected_by TEXT DEFAULT 'user',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_created
                    ON sessions(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_results_session
                    ON coded_results(session_id);
                CREATE INDEX IF NOT EXISTS idx_feedback_session
                    ON feedback(session_id);
            """)
            conn.commit()
        finally:
            conn.close()

    def save_session(self, session_id: str, note: str, note_type: str,
                     mode: str, status: str = "pending") -> str:
        """Save a session record. Encrypts PHI fields before storage."""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        enc = get_encryption()
        encrypted_note = enc.encrypt(note[:500])
        
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO sessions (id, clinical_note, note_type, mode, status)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, encrypted_note, note_type, mode, status),
            )
            conn.commit()
            return session_id
        finally:
            conn.close()

    def update_session(self, session_id: str, **kwargs):
        """Update session fields."""
        allowed = {"status", "processing_time_s", "confidence_overall",
                   "needs_human_review", "raw_response"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return
        
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [session_id]
        
        conn = self._get_conn()
        try:
            conn.execute(
                f"UPDATE sessions SET {set_clause} WHERE id = ?",
                values,
            )
            conn.commit()
        finally:
            conn.close()

    def save_results(self, session_id: str, results: list[dict]):
        """Save coded results for a session."""
        conn = self._get_conn()
        try:
            for i, r in enumerate(results):
                conn.execute(
                    """INSERT INTO coded_results
                       (session_id, code, code_name, vocabulary, code_type,
                        sequence_order, llm_score, is_billable, reasoning, confidence_level)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
            conn.commit()
        finally:
            conn.close()

    def save_feedback(self, session_id: str, code: str, action: str,
                      corrected_code: str = None, corrected_by: str = "user"):
        """Save user feedback on a coded result."""
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO feedback
                   (session_id, code, action, corrected_code, corrected_by)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, code, action, corrected_code, corrected_by),
            )
            conn.commit()
        finally:
            conn.close()

    def get_session(self, session_id: str, decrypt: bool = True) -> Optional[dict]:
        """Get a session by ID. Decrypts PHI fields if requested."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if row is None:
                return None
            
            session = dict(row)
            
            # Decrypt PHI fields
            if decrypt and session.get("clinical_note"):
                enc = get_encryption()
                try:
                    session["clinical_note"] = enc.decrypt(session["clinical_note"])
                except Exception:
                    pass
            
            # Get results
            results = conn.execute(
                "SELECT * FROM coded_results WHERE session_id = ? ORDER BY sequence_order",
                (session_id,),
            ).fetchall()
            session["results"] = [dict(r) for r in results]
            
            return session
        finally:
            conn.close()

    def get_history(self, limit: int = 20, offset: int = 0, decrypt: bool = True) -> list[dict]:
        """Get recent session history. Decrypts PHI fields if requested."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT id, created_at, clinical_note, note_type, mode, status,
                          processing_time_s, confidence_overall, needs_human_review
                   FROM sessions
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset),
            ).fetchall()
            sessions = [dict(r) for r in rows]
            
            if decrypt:
                enc = get_encryption()
                for s in sessions:
                    if s.get("clinical_note"):
                        try:
                            s["clinical_note"] = enc.decrypt(s["clinical_note"])
                        except Exception:
                            pass
            
            return sessions
        finally:
            conn.close()

    def get_stats(self) -> dict:
        """Get aggregated statistics."""
        conn = self._get_conn()
        try:
            total = conn.execute(
                "SELECT COUNT(*) as c FROM sessions"
            ).fetchone()["c"]
            
            today = conn.execute(
                """SELECT COUNT(*) as c FROM sessions
                   WHERE date(created_at) = date('now')"""
            ).fetchone()["c"]
            
            avg_confidence = conn.execute(
                """SELECT AVG(confidence_overall) as avg_conf
                   FROM sessions WHERE confidence_overall IS NOT NULL"""
            ).fetchone()["avg_conf"] or 0
            
            return {
                "total_sessions": total,
                "today_sessions": today,
                "avg_confidence": round(avg_confidence, 1),
            }
        finally:
            conn.close()

    def close(self):
        """Close any remaining connections (no-op for connection-per-operation)."""
        pass
