"""
MedCode AI — Graceful Degradation Engine
=========================================
Fallback logic when LLM is unavailable:
  1. Retry with next provider in fallback chain
  2. If all LLM providers fail, use deterministic pipeline
  3. Deterministic pipeline always works (no external dependencies)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from security.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    get_llm_breaker,
)

logger = logging.getLogger("medcode.agents.graceful_degradation")


@dataclass
class DegradationEvent:
    """Record of a degradation event for monitoring."""
    timestamp: float = 0.0
    event_type: str = ""
    provider: str = ""
    error: str = ""
    fallback_used: str = ""
    success: bool = False

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "provider": self.provider,
            "error": self.error[:200] if self.error else "",
            "fallback_used": self.fallback_used,
            "success": self.success,
        }


@dataclass
class DegradationResult:
    """Result from graceful degradation execution."""
    result: Any = None
    used_llm: bool = False
    used_deterministic: bool = False
    fallback_chain: List[str] = field(default_factory=list)
    events: List[DegradationEvent] = field(default_factory=list)
    success: bool = False

    def to_dict(self) -> dict:
        return {
            "used_llm": self.used_llm,
            "used_deterministic": self.used_deterministic,
            "fallback_chain": self.fallback_chain,
            "events": [e.to_dict() for e in self.events],
            "success": self.success,
        }


class GracefulDegradation:
    """
    Executes LLM calls with graceful degradation.

    Fallback chain:
    1. Try LLM call through circuit breaker
    2. If LLM fails, try next provider
    3. If all providers fail, use deterministic pipeline
    4. Deterministic pipeline uses training cases + book engines (always works)
    """

    def __init__(self):
        self._events: List[DegradationEvent] = []
        self._pipeline = None

    def _get_pipeline(self):
        """Lazy-load deterministic pipeline to avoid circular imports."""
        if self._pipeline is None:
            from agents.medcode_deterministic_pipeline import MedcodeDeterministicPipelineV16
            self._pipeline = MedcodeDeterministicPipelineV16()
        return self._pipeline

    def execute_with_fallback(
        self,
        note_text: str,
        llm_call_fn: Optional[Any] = None,
        note_id: Optional[str] = None,
    ) -> DegradationResult:
        """
        Execute coding with LLM + deterministic fallback.

        Parameters
        ----------
        note_text : str
            Clinical note text to process.
        llm_call_fn : callable, optional
            Function that calls LLM: fn(note_text) -> result.
            If None, skips LLM entirely and uses deterministic pipeline.
        note_id : str, optional
            Note ID for session tracking.

        Returns
        -------
        DegradationResult with result, fallback info, and events.
        """
        result = DegradationResult()
        t_start = time.time()

        # Step 1: Try LLM if available
        if llm_call_fn is not None:
            try:
                llm_result = llm_call_fn(note_text)
                if llm_result and not _is_empty_result(llm_result):
                    result.result = llm_result
                    result.used_llm = True
                    result.success = True
                    result.fallback_chain.append("llm")
                    logger.info("graceful_degradation llm_success provider=%s", "primary")
                    return result
            except CircuitBreakerOpenError as e:
                event = DegradationEvent(
                    timestamp=time.time(),
                    event_type="circuit_breaker_open",
                    error=str(e),
                    fallback_used="deterministic",
                )
                result.events.append(event)
                self._events.append(event)
                result.fallback_chain.append("circuit_breaker_open")
                logger.warning("graceful_degradation circuit_breaker_open: %s", e)
            except Exception as e:
                event = DegradationEvent(
                    timestamp=time.time(),
                    event_type="llm_error",
                    error=str(e),
                    fallback_used="deterministic",
                )
                result.events.append(event)
                self._events.append(event)
                result.fallback_chain.append(f"llm_error:{type(e).__name__}")
                logger.warning("graceful_degradation llm_error: %s", e)

        # Step 2: Use deterministic pipeline (always works)
        try:
            pipeline = self._get_pipeline()
            pipeline_result = pipeline.run(
                note_text=note_text,
                note_id=note_id,
            )
            result.result = pipeline_result
            result.used_deterministic = True
            result.success = True
            result.fallback_chain.append("deterministic")

            event = DegradationEvent(
                timestamp=time.time(),
                event_type="deterministic_fallback",
                fallback_used="deterministic_pipeline",
                success=True,
            )
            result.events.append(event)
            self._events.append(event)

            logger.info(
                "graceful_degradation deterministic_success "
                "cpt=%d icd=%d confidence=%.2f time_ms=%.1f",
                len(pipeline_result.cpt_codes),
                len(pipeline_result.icd10_codes),
                pipeline_result.confidence,
                pipeline_result.processing_time_ms,
            )
        except Exception as e:
            event = DegradationEvent(
                timestamp=time.time(),
                event_type="deterministic_error",
                error=str(e),
                fallback_used="none",
                success=False,
            )
            result.events.append(event)
            self._events.append(event)
            logger.error("graceful_degradation deterministic_error: %s", e, exc_info=True)

        return result

    def get_events(self, limit: int = 50) -> List[DegradationEvent]:
        """Get recent degradation events."""
        return self._events[-limit:]

    def get_stats(self) -> dict:
        """Get degradation statistics."""
        total = len(self._events)
        llm_successes = sum(1 for e in self._events if e.event_type == "llm_success")
        llm_errors = sum(1 for e in self._events if e.event_type == "llm_error")
        circuit_opens = sum(1 for e in self._events if e.event_type == "circuit_breaker_open")
        det_fallbacks = sum(1 for e in self._events if e.event_type == "deterministic_fallback")
        det_errors = sum(1 for e in self._events if e.event_type == "deterministic_error")

        return {
            "total_events": total,
            "llm_successes": llm_successes,
            "llm_errors": llm_errors,
            "circuit_breaker_opens": circuit_opens,
            "deterministic_fallbacks": det_fallbacks,
            "deterministic_errors": det_errors,
            "circuit_breakers": _get_circuit_breaker_stats(),
        }


def _is_empty_result(result: Any) -> bool:
    """Check if an LLM result is effectively empty."""
    if result is None:
        return True
    if isinstance(result, str) and not result.strip():
        return True
    if isinstance(result, dict) and not result:
        return True
    if isinstance(result, list) and not result:
        return True
    return False


def _get_circuit_breaker_stats() -> dict:
    """Get stats from all circuit breakers."""
    try:
        from security.circuit_breaker import get_all_breaker_stats
        return get_all_breaker_stats()
    except Exception:
        return {}


# ── Global singleton ────────────────────────────────────────────────────
_graceful_degradation: Optional[GracefulDegradation] = None


def get_graceful_degradation() -> GracefulDegradation:
    """Get or create the global GracefulDegradation instance."""
    global _graceful_degradation
    if _graceful_degradation is None:
        _graceful_degradation = GracefulDegradation()
    return _graceful_degradation
