"""Enterprise Circuit Breaker Pattern.

Monitors outbound LLM provider health. If an endpoint throws consecutive errors
(HTTP 429 Too Many Requests, HTTP 500/503, or timeouts), the circuit trips to OPEN,
instantly rerouting traffic to fallback models without waiting for repeated timeouts.
"""

import time
from enum import Enum
from typing import Optional


class CircuitState(str, Enum):
    CLOSED = "CLOSED"        # Normal operations: healthy
    OPEN = "OPEN"            # Tripped: all requests immediately diverted to fallback
    HALF_OPEN = "HALF_OPEN"  # Testing recovery: single probe request allowed


class CircuitBreaker:
    """Tracks error rates and state transitions for an individual LLM provider."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 10.0
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.state: CircuitState = CircuitState.CLOSED
        self.consecutive_failures: int = 0
        self.last_failure_time: Optional[float] = None

    def can_execute(self) -> bool:
        """Determines if the provider is eligible to receive requests."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if cooldown has elapsed to attempt recovery
            if self.last_failure_time and (time.time() - self.last_failure_time) >= self.recovery_timeout_seconds:
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def record_success(self):
        """Resets the circuit breaker upon a successful execution."""
        self.consecutive_failures = 0
        self.state = CircuitState.CLOSED

    def record_failure(self):
        """Records a failure (e.g. HTTP 429 or 5xx) and trips the circuit if threshold exceeded."""
        self.consecutive_failures += 1
        self.last_failure_time = time.time()

        if self.consecutive_failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
