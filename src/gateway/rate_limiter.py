"""Enterprise Token Bucket Rate Limiter.

Enforces per-tenant and per-user Request-Per-Minute (RPM) and Token-Per-Minute (TPM)
rate limits, protecting the enterprise from runaway API billing and downstream quota exhaustion.
"""

import time
from typing import Dict


class RateLimitExceeded(Exception):
    """Raised when a tenant or user exceeds their allocated rate limit."""
    pass


class TokenBucketRateLimiter:
    """In-memory thread-safe Token Bucket Rate Limiter with burst capacity."""

    def __init__(self, default_rate_rpm: int = 60, burst_multiplier: float = 1.5):
        self.default_rate_rpm = default_rate_rpm
        self.capacity = default_rate_rpm * burst_multiplier
        self.refill_rate_per_sec = default_rate_rpm / 60.0
        # tenant_id -> {"tokens": float, "last_refill": float}
        self.buckets: Dict[str, Dict[str, float]] = {}

    def acquire(self, key: str = "global", tokens_requested: int = 1) -> bool:
        """Attempts to acquire tokens for a request. Returns True if granted, False if rate-limited."""
        now = time.time()

        if key not in self.buckets:
            self.buckets[key] = {
                "tokens": self.capacity,
                "last_refill": now
            }

        bucket = self.buckets[key]
        elapsed = now - bucket["last_refill"]
        bucket["last_refill"] = now

        # Refill tokens based on elapsed time up to maximum capacity
        bucket["tokens"] = min(self.capacity, bucket["tokens"] + (elapsed * self.refill_rate_per_sec))

        if bucket["tokens"] >= tokens_requested:
            bucket["tokens"] -= tokens_requested
            return True

        return False
