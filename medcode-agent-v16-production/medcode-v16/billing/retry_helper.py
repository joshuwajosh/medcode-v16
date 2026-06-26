"""
Billing Retry Helper — Exponential Backoff for Billing Operations
================================================================
Provides retry logic with exponential backoff for:
  - EDI submission
  - Webhook delivery
  - Claim tracking operations
"""
from __future__ import annotations

import logging
import time
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

logger = logging.getLogger("medcode.billing.retry")


@dataclass
class RetryConfig:
    """Configuration for billing retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_range: float = 0.1
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)

    def to_dict(self) -> dict:
        return {
            "max_retries": self.max_retries,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "exponential_base": self.exponential_base,
            "jitter": self.jitter,
        }


@dataclass
class RetryResult:
    """Result of a retry operation."""
    success: bool = False
    attempts: int = 0
    total_delay: float = 0.0
    last_error: str = ""
    result: Any = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "attempts": self.attempts,
            "total_delay": round(self.total_delay, 3),
            "last_error": self.last_error,
        }


# Preset configs for common billing operations
EDI_SUBMISSION_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=2.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True,
    retryable_exceptions=(ConnectionError, TimeoutError, OSError),
)

WEBHOOK_DELIVERY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=25.0,
    exponential_base=2.0,
    jitter=True,
    retryable_exceptions=(ConnectionError, TimeoutError, OSError),
)

CLAIM_TRACKING_CONFIG = RetryConfig(
    max_retries=2,
    base_delay=1.0,
    max_delay=10.0,
    exponential_base=2.0,
    jitter=False,
    retryable_exceptions=(ConnectionError, TimeoutError),
)


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay for a retry attempt with exponential backoff.

    Args:
        attempt: Current attempt number (0-based).
        config: The retry configuration.

    Returns:
        Delay in seconds.
    """
    delay = config.base_delay * (config.exponential_base ** attempt)
    delay = min(delay, config.max_delay)
    if config.jitter:
        jitter_amount = delay * config.jitter_range
        delay += random.uniform(-jitter_amount, jitter_amount)
        delay = max(0.1, delay)
    return delay


def retry_with_backoff(
    fn: Callable,
    *args: Any,
    config: Optional[RetryConfig] = None,
    operation_name: str = "billing_operation",
    **kwargs: Any,
) -> RetryResult:
    """Execute a function with retry logic and exponential backoff.

    Args:
        fn: The function to execute.
        *args: Positional arguments for fn.
        config: Retry configuration (defaults to generic config).
        operation_name: Name for logging purposes.
        **kwargs: Keyword arguments for fn.

    Returns:
        RetryResult with execution outcome.
    """
    active_config = config or RetryConfig()
    result = RetryResult()

    for attempt in range(active_config.max_retries + 1):
        try:
            value = fn(*args, **kwargs)
            result.success = True
            result.attempts = attempt + 1
            result.result = value
            if attempt > 0:
                logger.info(
                    "[%s] Succeeded after %d attempts (%.2fs total delay)",
                    operation_name, attempt + 1, result.total_delay,
                )
            return result
        except active_config.retryable_exceptions as exc:
            result.last_error = str(exc)
            result.attempts = attempt + 1

            if attempt < active_config.max_retries:
                delay = calculate_delay(attempt, active_config)
                result.total_delay += delay
                logger.warning(
                    "[%s] Attempt %d/%d failed: %s. Retrying in %.2fs...",
                    operation_name, attempt + 1, active_config.max_retries + 1,
                    str(exc)[:200], delay,
                )
                time.sleep(delay)
            else:
                logger.error(
                    "[%s] All %d attempts exhausted. Last error: %s",
                    operation_name, active_config.max_retries + 1, str(exc)[:200],
                )

    return result


def retry_edi_submission(fn: Callable, *args: Any, **kwargs: Any) -> RetryResult:
    """Retry wrapper specifically for EDI submission operations."""
    return retry_with_backoff(
        fn, *args,
        config=EDI_SUBMISSION_CONFIG,
        operation_name="edi_submission",
        **kwargs,
    )


def retry_webhook_delivery(fn: Callable, *args: Any, **kwargs: Any) -> RetryResult:
    """Retry wrapper specifically for webhook delivery."""
    return retry_with_backoff(
        fn, *args,
        config=WEBHOOK_DELIVERY_CONFIG,
        operation_name="webhook_delivery",
        **kwargs,
    )


def retry_claim_tracking(fn: Callable, *args: Any, **kwargs: Any) -> RetryResult:
    """Retry wrapper specifically for claim tracking operations."""
    return retry_with_backoff(
        fn, *args,
        config=CLAIM_TRACKING_CONFIG,
        operation_name="claim_tracking",
        **kwargs,
    )
