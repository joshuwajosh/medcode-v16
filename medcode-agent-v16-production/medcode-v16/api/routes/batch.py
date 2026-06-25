"""
MedCode AI V19 — Batch Claim Processing API Routes
=====================================================
Endpoints for submitting, monitoring, and retrying
batch claim processing jobs.
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

router = APIRouter(prefix="/api/v19/billing", tags=["batch"])


class BatchClaimInput(BaseModel):
    cpt_codes: List[Dict[str, Any]]
    icd_codes: List[Dict[str, Any]]
    patient_info: Optional[Dict[str, Any]] = None
    provider_info: Optional[Dict[str, Any]] = None


class BatchSubmitRequest(BaseModel):
    claims: List[BatchClaimInput] = Field(..., min_length=1, max_length=100)


def _get_processor():
    from billing.batch_processor import BatchClaimProcessor
    return BatchClaimProcessor()


def _process_in_background(batch_id: str, claims: List[Dict[str, Any]]):
    processor = _get_processor()
    processor.process_batch(claims)


@router.post("/batch")
async def submit_batch(body: BatchSubmitRequest, background_tasks: BackgroundTasks):
    """Submit a batch of claims for processing. Runs in background."""
    processor = _get_processor()

    claim_dicts = []
    for c in body.claims:
        claim_dicts.append({
            "cpt_codes": c.cpt_codes,
            "icd_codes": c.icd_codes,
            "patient_info": c.patient_info or {},
            "provider_info": c.provider_info or {},
        })

    result = processor.process_batch(claim_dicts)

    return {
        "batch_id": result.batch_id,
        "total_claims": result.total_claims,
        "status": "processing",
        "message": "Batch submitted. Use GET /batch/{batch_id} to check status.",
    }


@router.get("/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    """Get the current status of a batch processing job."""
    processor = _get_processor()
    status = processor.get_batch_status(batch_id)

    if not status:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")

    return status.to_dict()


@router.get("/batches")
async def list_batches(limit: int = 20):
    """List recent batch processing jobs."""
    processor = _get_processor()
    batches = processor.list_batches(limit=limit)
    return {
        "batches": [b.to_dict() for b in batches],
        "count": len(batches),
    }


@router.post("/batch/{batch_id}/retry")
async def retry_failed_claims(batch_id: str, background_tasks: BackgroundTasks):
    """Retry failed claims in a batch."""
    processor = _get_processor()
    status = processor.get_batch_status(batch_id)

    if not status:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")

    if status.failed == 0:
        raise HTTPException(status_code=400, detail="No failed claims to retry in this batch")

    conn = processor._conn()
    try:
        rows = conn.execute(
            "SELECT result_json FROM batch_claims "
            "WHERE batch_id=? AND status='failed'",
            (batch_id,),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        raise HTTPException(status_code=400, detail="No failed claims found")

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
        raise HTTPException(status_code=400, detail="Could not parse failed claims for retry")

    retry_result = processor.process_batch(retry_claims)

    return {
        "original_batch_id": batch_id,
        "retry_batch_id": retry_result.batch_id,
        "retry_claims_count": len(retry_claims),
        "status": "processing",
        "message": "Retry batch submitted. Use GET /batch/{retry_batch_id} to check status.",
    }
