"""
MedCode AI V19 — Batch Claim Processing Models
=================================================
Dataclasses for batch claim processing results, status, and summaries.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ClaimResult:
    """Result of processing a single claim within a batch."""
    claim_id: str = ""
    success: bool = True
    error: Optional[str] = None
    validation_passed: bool = False
    denial_risk: str = "low"
    denial_probability: float = 0.0
    edi_generated: bool = False
    edi_type: str = ""
    total_charges: float = 0.0
    processing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "success": self.success,
            "error": self.error,
            "validation_passed": self.validation_passed,
            "denial_risk": self.denial_risk,
            "denial_probability": self.denial_probability,
            "edi_generated": self.edi_generated,
            "edi_type": self.edi_type,
            "total_charges": self.total_charges,
            "processing_time_ms": round(self.processing_time_ms, 2),
        }


@dataclass
class BatchResult:
    """Complete result of a batch claim processing run."""
    batch_id: str = ""
    total_claims: int = 0
    successful: int = 0
    failed: int = 0
    processing_time: float = 0.0
    created_at: str = ""
    completed_at: str = ""
    results: List[ClaimResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "total_claims": self.total_claims,
            "successful": self.successful,
            "failed": self.failed,
            "processing_time": round(self.processing_time, 3),
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "results": [r.to_dict() for r in self.results],
        }


@dataclass
class BatchStatus:
    """Current status of a batch processing job."""
    batch_id: str = ""
    status: str = "pending"  # pending | processing | completed | failed
    progress_pct: float = 0.0
    total_claims: int = 0
    processed: int = 0
    successful: int = 0
    failed: int = 0
    created_at: str = ""
    updated_at: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "status": self.status,
            "progress_pct": round(self.progress_pct, 1),
            "total_claims": self.total_claims,
            "processed": self.processed,
            "successful": self.successful,
            "failed": self.failed,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
        }


@dataclass
class BatchSummary:
    """Summary record for a batch, used in list views."""
    batch_id: str = ""
    created_at: str = ""
    total_claims: int = 0
    status: str = "pending"
    success_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "created_at": self.created_at,
            "total_claims": self.total_claims,
            "status": self.status,
            "success_rate": round(self.success_rate, 1),
        }
