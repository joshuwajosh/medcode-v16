"""
MedCode AI — Circuit Breaker for LLM API Calls
================================================
Protects against cascading failures when LLM providers are down.
States: CLOSED (normal) -> OPEN (failing) -> HALF_OPEN (testing recovery).
"""

from __future__ import annotations

import threading
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger("medcode.security.circuit_breaker")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerStats:
    """Tracks circuit breaker metrics."""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    state_transitions: list = field(default_factory=list)
    total_calls: int = 0
    total_rejected: int = 0

    def to_dict(self) -> dict:
        return {
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_calls": self.total_calls,
            "total_rejected": self.total_rejected,
            "state_transitions": self.state_transitions[-10:],
        }


class CircuitBreaker:
    """
    Circuit breaker pattern for protecting LLM API calls.

    States:
        CLOSED: Normal operation. Calls pass through.
                After `failure_threshold` consecutive failures -> OPEN.
        OPEN: All calls rejected immediately with fallback response.
              After `recovery_timeout` seconds -> HALF_OPEN.
        HALF_OPEN: One test call allowed.
                   If success -> CLOSED. If fail -> OPEN.
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 1,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()
        self._half_open_calls = 0
        self._consecutive_failures = 0

    @property
    def state(self) -> CircuitState:
        """Check if OPEN state has timed out -> transition to HALF_OPEN."""
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._stats.last_failure_time
            if elapsed >= self.recovery_timeout:
                self._transition(CircuitState.HALF_OPEN)
        return self._state

    def _transition(self, new_state: CircuitState) -> None:
        old = self._state
        self._state = new_state
        transition = {
            "from": old.value,
            "to": new_state.value,
            "time": time.time(),
        }
        self._stats.state_transitions.append(transition)
        logger.info(
            "circuit_breaker[%s] state_transition %s -> %s",
            self.name, old.value, new_state.value,
        )

    def record_success(self) -> None:
        """Record a successful call."""
        self._stats.success_count += 1
        self._stats.total_calls += 1
        self._stats.last_success_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._consecutive_failures = 0
            self._half_open_calls = 0
            self._transition(CircuitState.CLOSED)
        elif self._state == CircuitState.CLOSED:
            self._consecutive_failures = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        self._stats.failure_count += 1
        self._stats.total_calls += 1
        self._stats.last_failure_time = time.time()
        self._consecutive_failures += 1

        if self._state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self._transition(CircuitState.OPEN)
        elif self._state == CircuitState.CLOSED:
            if self._consecutive_failures >= self.failure_threshold:
                self._transition(CircuitState.OPEN)

    def should_allow(self) -> bool:
        """Check if a call should be allowed through."""
        current = self.state  # triggers timeout check
        if current == CircuitState.CLOSED:
            return True
        if current == CircuitState.OPEN:
            self._stats.total_rejected += 1
            return False
        if current == CircuitState.HALF_OPEN:
            if self._half_open_calls < self.half_open_max_calls:
                self._half_open_calls += 1
                return True
            self._stats.total_rejected += 1
            return False
        return False

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.

        Parameters
        ----------
        func : Callable
            The function to call.
        *args, **kwargs
            Arguments to pass to the function.

        Returns
        -------
        Result of func, or raises CircuitBreakerOpenError if blocked.

        Raises
        ------
        CircuitBreakerOpenError
            If circuit is OPEN and call is rejected.
        """
        if not self.should_allow():
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Recovery in {self._time_until_recovery():.0f}s."
            )
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise

    def _time_until_recovery(self) -> float:
        """Seconds until recovery timeout expires."""
        if self._state != CircuitState.OPEN:
            return 0.0
        elapsed = time.time() - self._stats.last_failure_time
        remaining = self.recovery_timeout - elapsed
        return max(0.0, remaining)

    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "consecutive_failures": self._consecutive_failures,
            "time_until_recovery": round(self._time_until_recovery(), 1),
            **self._stats.to_dict(),
        }

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED."""
        previous_state = self._state
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._half_open_calls = 0
        self._stats.state_transitions.append({
            "from": previous_state.value,
            "to": "closed",
            "time": time.time(),
            "reason": "manual_reset",
        })
        logger.info("circuit_breaker[%s] manually reset %s -> CLOSED", self.name, previous_state.value)


class CircuitBreakerOpenError(Exception):
    """Raised when a call is rejected by an open circuit breaker."""
    pass


# ── Global circuit breakers for LLM providers ──────────────────────────
_llm_breakers: dict[str, CircuitBreaker] = {}
_llm_breakers_lock = threading.Lock()


def get_llm_breaker(provider: str) -> CircuitBreaker:
    """Get or create a circuit breaker for an LLM provider."""
    if provider not in _llm_breakers:
        with _llm_breakers_lock:
            if provider not in _llm_breakers:
                _llm_breakers[provider] = CircuitBreaker(
                    name=f"llm_{provider}",
                    failure_threshold=5,
                    recovery_timeout=60.0,
                )
    return _llm_breakers[provider]


def get_all_breaker_stats() -> dict:
    """Get stats for all LLM circuit breakers."""
    return {name: cb.get_stats() for name, cb in _llm_breakers.items()}
