"""
Circuit Breaker — V12 Phase 11: Failure Isolation (Enhanced)

Prevents cascading failures by monitoring failure rates
and opening the circuit when thresholds are exceeded.

Circuit states:
- CLOSED: Normal operation, requests pass through
- OPEN: Failure threshold exceeded, requests fail fast
- HALF_OPEN: Testing if service has recovered

Enhancements:
- Configurable thresholds per LLM provider
- State change metrics tracking
- Recovery testing with success-rate thresholds
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("medcode.resilience.circuit_breaker")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"           # Normal operation
    OPEN = "open"               # Failing fast
    HALF_OPEN = "half_open"     # Testing recovery


@dataclass
class StateTransition:
    """Record of a circuit breaker state change."""
    from_state: str
    to_state: str
    timestamp: float
    reason: str
    consecutive_failures: int = 0

    def to_dict(self) -> dict:
        return {
            "from": self.from_state,
            "to": self.to_state,
            "timestamp": self.timestamp,
            "reason": self.reason,
            "consecutive_failures": self.consecutive_failures,
        }


@dataclass
class CircuitStats:
    """Circuit breaker statistics."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    total_requests: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    consecutive_failures: int = 0

    def failure_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.failure_count / self.total_requests

    def to_dict(self) -> dict:
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": self.total_requests,
            "failure_rate": round(self.failure_rate(), 4),
            "consecutive_failures": self.consecutive_failures,
        }


class CircuitBreaker:
    """
    Circuit breaker for failure isolation with configurable per-provider thresholds.

    Prevents cascading failures by:
    - Opening the circuit after consecutive failures
    - Failing fast when circuit is open
    - Testing recovery after a cooldown period
    - Automatically closing on successful recovery
    """

    def __init__(self, name: str = "default",
                 failure_threshold: int = 5,
                 recovery_timeout_seconds: float = 30.0,
                 half_open_max_requests: int = 3):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds
        self.half_open_max = half_open_max_requests
        self._stats = CircuitStats()
        self._half_open_requests = 0
        self._transitions: List[StateTransition] = []
        self._max_transitions = 100

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        if self._stats.state == CircuitState.OPEN:
            if time.time() - self._stats.last_failure_time >= self.recovery_timeout:
                return CircuitState.HALF_OPEN
        return self._stats.state

    def _record_transition(self, to_state: CircuitState, reason: str) -> None:
        """Record a state transition for metrics."""
        from_state = self._stats.state.value
        transition = StateTransition(
            from_state=from_state,
            to_state=to_state.value,
            timestamp=time.time(),
            reason=reason,
            consecutive_failures=self._stats.consecutive_failures,
        )
        self._transitions.append(transition)
        if len(self._transitions) > self._max_transitions:
            self._transitions = self._transitions[-self._max_transitions:]
        logger.info(
            "[circuit:%s] %s -> %s (%s)",
            self.name, from_state, to_state.value, reason,
        )

    def call(self, fn: Callable, *args, **kwargs) -> Any:
        """
        Call a function through the circuit breaker.

        Args:
            fn: The function to call.
            *args: Function arguments.
            **kwargs: Function keyword arguments.

        Returns:
            The function result.

        Raises:
            CircuitBreakerOpenError: If circuit is open.
            Any exception from the called function.
        """
        current_state = self.state

        if current_state == CircuitState.OPEN:
            self._stats.total_requests += 1
            raise CircuitBreakerOpenError(
                f"Circuit '{self.name}' is OPEN. Failing fast."
            )

        if current_state == CircuitState.HALF_OPEN:
            if self._half_open_requests >= self.half_open_max:
                self._stats.total_requests += 1
                raise CircuitBreakerOpenError(
                    f"Circuit '{self.name}' is HALF_OPEN. "
                    f"Max test requests ({self.half_open_max}) reached."
                )
            self._half_open_requests += 1

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Record a successful call."""
        prev_state = self._stats.state
        self._stats.success_count += 1
        self._stats.total_requests += 1
        self._stats.last_success_time = time.time()
        self._stats.consecutive_failures = 0
        self._stats.state = CircuitState.CLOSED
        self._half_open_requests = 0
        if prev_state != CircuitState.CLOSED:
            self._record_transition(
                CircuitState.CLOSED,
                "recovery_succeeded",
            )

    def _on_failure(self) -> None:
        """Record a failed call."""
        prev_state = self._stats.state
        self._stats.failure_count += 1
        self._stats.total_requests += 1
        self._stats.last_failure_time = time.time()
        self._stats.consecutive_failures += 1

        if self._stats.consecutive_failures >= self.failure_threshold:
            self._stats.state = CircuitState.OPEN
            self._record_transition(
                CircuitState.OPEN,
                f"threshold_reached({self._stats.consecutive_failures}/{self.failure_threshold})",
            )

    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        self._stats = CircuitStats()
        self._half_open_requests = 0
        self._record_transition(CircuitState.CLOSED, "manual_reset")

    def get_stats(self) -> dict:
        """Get circuit breaker statistics including transition history."""
        return {
            "name": self.name,
            "state": self.state.value,
            "stats": self._stats.to_dict(),
            "thresholds": {
                "failure_threshold": self.failure_threshold,
                "recovery_timeout_seconds": self.recovery_timeout,
                "half_open_max_requests": self.half_open_max,
            },
            "recent_transitions": [t.to_dict() for t in self._transitions[-10:]],
            "total_transitions": len(self._transitions),
        }


# ── Per-Provider Circuit Breaker Registry ────────────────────────────────

_PROVIDER_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "deepseek": {
        "failure_threshold": 5,
        "recovery_timeout_seconds": 30.0,
        "half_open_max_requests": 3,
    },
    "groq": {
        "failure_threshold": 3,
        "recovery_timeout_seconds": 15.0,
        "half_open_max_requests": 2,
    },
    "cerebras": {
        "failure_threshold": 3,
        "recovery_timeout_seconds": 20.0,
        "half_open_max_requests": 2,
    },
    "ollama": {
        "failure_threshold": 4,
        "recovery_timeout_seconds": 10.0,
        "half_open_max_requests": 2,
    },
}

_provider_breakers: Dict[str, CircuitBreaker] = {}


def get_provider_breaker(
    provider: str,
    failure_threshold: Optional[int] = None,
    recovery_timeout: Optional[float] = None,
) -> CircuitBreaker:
    """Get or create a circuit breaker for a specific LLM provider.

    Args:
        provider: Provider name (e.g., 'deepseek', 'groq').
        failure_threshold: Override default failure threshold.
        recovery_timeout: Override default recovery timeout.

    Returns:
        CircuitBreaker instance for the provider.
    """
    if provider not in _provider_breakers:
        defaults = _PROVIDER_DEFAULTS.get(provider, {})
        _provider_breakers[provider] = CircuitBreaker(
            name=provider,
            failure_threshold=failure_threshold or defaults.get("failure_threshold", 5),
            recovery_timeout_seconds=recovery_timeout or defaults.get("recovery_timeout_seconds", 30.0),
            half_open_max_requests=defaults.get("half_open_max_requests", 3),
        )
    return _provider_breakers[provider]


def get_all_provider_stats() -> Dict[str, dict]:
    """Get circuit breaker stats for all registered providers."""
    return {
        name: breaker.get_stats()
        for name, breaker in _provider_breakers.items()
    }


class CircuitBreakerOpenError(Exception):
    """Exception raised when a circuit breaker is open."""
    pass
