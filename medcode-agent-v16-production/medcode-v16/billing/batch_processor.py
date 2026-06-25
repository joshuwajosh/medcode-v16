"""
MedCode AI V19 — Batch Claim Processor
========================================
Processes multiple claims in a single batch with validation,
denial prediction, EDI generation, and tracking.
"""
from __future__ import annotations

import os
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from billing.batch_models import BatchResult, BatchStatus, BatchSummary, ClaimResult
from billing.claim_engine import (
    Claim,
    ClaimGenerator,
    ClaimValidator,
    DenialPredictor,
    get_claim_generator,
    get_claim_validator,
    get_denial_predictor,
)
from billing.edi_837 import EDI837Generator

DEFAULT_DB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BatchClaimProcessor:
    """
    Processes batches of claims with per-claim validation,
    denial prediction, EDI generation, and status tracking.
    """

    def __init__(self, db_dir: Optional[str] = None):
        self.db_dir = db_dir or DEFAULT_DB_DIR
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, "batches.db")
        self._lock = threading.Lock()
        self._init_db()
        self._generator: Optional[ClaimGenerator] = None
        self._validator: Optional[ClaimValidator] = None
        self._predictor: Optional[DenialPredictor] = None
        self._edi_gen: Optional[EDI837Generator] = None

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS batches (
                    batch_id TEXT PRIMARY KEY,
                    organization_id TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending',
                    total_claims INTEGER DEFAULT 0,
                    processed INTEGER DEFAULT 0,
                    successful INTEGER DEFAULT 0,
                    failed INTEGER DEFAULT 0,
                    progress_pct REAL DEFAULT 0.0,
                    created_at TEXT,
                    updated_at TEXT,
                    completed_at TEXT,
                    error TEXT,
                    result_json TEXT
                );

                CREATE TABLE IF NOT EXISTS batch_claims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT NOT NULL,
                    claim_index INTEGER NOT NULL,
                    claim_id TEXT,
                    status TEXT DEFAULT 'pending',
                    result_json TEXT,
                    FOREIGN KEY (batch_id) REFERENCES batches(batch_id)
                );
            """)
            conn.commit()

            # Migration: add organization_id column if missing
            try:
                conn.execute("ALTER TABLE batches ADD COLUMN organization_id TEXT DEFAULT ''")
                conn.commit()
            except Exception:
                pass  # Column already exists
        finally:
            conn.close()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_generators(self):
        if self._generator is None:
            self._generator = get_claim_generator()
            self._validator = get_claim_validator()
            self._predictor = get_denial_predictor()
            self._edi_gen = EDI837Generator()
        return self._generator, self._validator, self._predictor, self._edi_gen

    def process_batch(
        self,
        claims: List[Dict[str, Any]],
        callback: Optional[Callable[[int, int, str], None]] = None,
        organization_id: str = "",
    ) -> BatchResult:
        """
        Process a list of claim dicts. Non-blocking: returns immediately
        and updates status in the DB. Use get_batch_status() to poll.
        """
        batch_id = f"BATCH-{uuid.uuid4().hex[:12].upper()}"
        now = _now_iso()

        result = BatchResult(
            batch_id=batch_id,
            total_claims=len(claims),
            created_at=now,
        )

        with self._lock:
            conn = self._conn()
            try:
                conn.execute(
                    "INSERT INTO batches (batch_id, organization_id, status, total_claims, created_at, updated_at) "
                    "VALUES (?, ?, 'processing', ?, ?, ?)",
                    (batch_id, organization_id, len(claims), now, now),
                )
                for idx, claim_data in enumerate(claims):
                    conn.execute(
                        "INSERT INTO batch_claims (batch_id, claim_index, claim_id, status) "
                        "VALUES (?, ?, ?, 'pending')",
                        (batch_id, idx, claim_data.get("claim_id", f"pending-{idx}")),
                    )
                conn.commit()
            finally:
                conn.close()

        thread = threading.Thread(
            target=self._process_batch_worker,
            args=(batch_id, claims, callback, result),
            daemon=True,
        )
        thread.start()

        return result

    def _process_batch_worker(
        self,
        batch_id: str,
        claims: List[Dict[str, Any]],
        callback: Optional[Callable],
        result: BatchResult,
    ):
        start = time.time()
        gen, validator, predictor, edi_gen = self._get_generators()
        successful = 0
        failed = 0

        for idx, claim_data in enumerate(claims):
            claim_start = time.time()
            claim_result = ClaimResult()

            try:
                cpt_codes = claim_data.get("cpt_codes", [])
                icd_codes = claim_data.get("icd_codes", [])
                patient_info = claim_data.get("patient_info", {})
                provider_info = claim_data.get("provider_info", {})

                claim = gen.generate_claim(
                    cpt_codes=cpt_codes,
                    icd_codes=icd_codes,
                    patient_info=patient_info,
                    provider_info=provider_info,
                )
                claim_result.claim_id = claim.claim_id
                claim_result.total_charges = claim.total_charges

                validation = validator.validate(claim)
                claim_result.validation_passed = validation.passed

                denial = predictor.predict_denial(claim, validation)
                claim_result.denial_risk = denial.risk_level
                claim_result.denial_probability = denial.denial_probability

                edi_type = "837I" if claim.claim_type == "institutional" else "837P"
                if edi_type == "837I":
                    edi_gen.generate_837i(claim)
                else:
                    edi_gen.generate_837p(claim)
                claim_result.edi_generated = True
                claim_result.edi_type = edi_type

                claim_result.success = True
                successful += 1

            except Exception as e:
                claim_result.success = False
                claim_result.error = str(e)
                failed += 1

            claim_result.processing_time_ms = (time.time() - claim_start) * 1000
            result.results.append(claim_result)

            processed = idx + 1
            pct = (processed / len(claims)) * 100 if claims else 100

            with self._lock:
                conn = self._conn()
                try:
                    conn.execute(
                        "UPDATE batches SET processed=?, successful=?, failed=?, "
                        "progress_pct=?, updated_at=? WHERE batch_id=?",
                        (processed, successful, failed, pct, _now_iso(), batch_id),
                    )
                    conn.execute(
                        "UPDATE batch_claims SET claim_id=?, status=?, result_json=? "
                        "WHERE batch_id=? AND claim_index=?",
                        (
                            claim_result.claim_id,
                            "success" if claim_result.success else "failed",
                            str(claim_result.to_dict()),
                            batch_id,
                            idx,
                        ),
                    )
                    conn.commit()
                finally:
                    conn.close()

            if callback:
                try:
                    callback(processed, len(claims), claim_result.claim_id)
                except Exception:
                    pass

        elapsed = time.time() - start
        result.successful = successful
        result.failed = failed
        result.processing_time = elapsed
        result.completed_at = _now_iso()

        final_status = "completed" if failed == 0 else ("failed" if successful == 0 else "completed")

        with self._lock:
            conn = self._conn()
            try:
                conn.execute(
                    "UPDATE batches SET status=?, successful=?, failed=?, "
                    "progress_pct=100.0, completed_at=?, updated_at=?, result_json=? "
                    "WHERE batch_id=?",
                    (
                        final_status,
                        successful,
                        failed,
                        result.completed_at,
                        result.completed_at,
                        str(result.to_dict()),
                        batch_id,
                    ),
                )
                conn.commit()
            finally:
                conn.close()

    def get_batch_status(self, batch_id: str) -> Optional[BatchStatus]:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM batches WHERE batch_id=?", (batch_id,)
            ).fetchone()
            if not row:
                return None
            return BatchStatus(
                batch_id=row["batch_id"],
                status=row["status"],
                progress_pct=row["progress_pct"],
                total_claims=row["total_claims"],
                processed=row["processed"],
                successful=row["successful"],
                failed=row["failed"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                error=row["error"],
            )
        finally:
            conn.close()

    def list_batches(self, limit: int = 20, organization_id: Optional[str] = None) -> List[BatchSummary]:
        conn = self._conn()
        try:
            query = ("SELECT batch_id, created_at, total_claims, status, "
                     "successful, failed FROM batches")
            params: list = []
            if organization_id:
                query += " WHERE organization_id = ?"
                params.append(organization_id)
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(query, params).fetchall()
            summaries = []
            for row in rows:
                total = row["total_claims"] or 0
                ok = row["successful"] or 0
                rate = (ok / total * 100) if total > 0 else 0.0
                summaries.append(BatchSummary(
                    batch_id=row["batch_id"],
                    created_at=row["created_at"],
                    total_claims=total,
                    status=row["status"],
                    success_rate=rate,
                ))
            return summaries
        finally:
            conn.close()

    def retry_failed(self, batch_id: str, callback: Optional[Callable] = None) -> Optional[BatchResult]:
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT result_json FROM batch_claims "
                "WHERE batch_id=? AND status='failed'",
                (batch_id,),
            ).fetchall()
        finally:
            conn.close()

        if not rows:
            return None

        retry_claims = []
        for row in rows:
            try:
                import ast
                result_data = ast.literal_eval(row["result_json"])
                claim_id = result_data.get("claim_id", "")
                if claim_id:
                    retry_claims.append({"claim_id": claim_id, "retry": True})
            except Exception:
                continue

        if not retry_claims:
            return None

        return self.process_batch(retry_claims, callback=callback)
