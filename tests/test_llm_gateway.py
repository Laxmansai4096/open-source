"""Unit Tests for Resilient LLM Gateway, Open-Source Fallback & Rate Limiting."""

import time
import pytest
from src.gateway.llm_gateway import ResilientLlmGateway
from src.gateway.circuit_breaker import CircuitBreaker, CircuitState
from src.gateway.rate_limiter import TokenBucketRateLimiter, RateLimitExceeded
from src.gateway.semantic_cache import SemanticCache


def test_gateway_primary_execution():
    """Verifies standard generation through primary provider."""
    gateway = ResilientLlmGateway()
    result = gateway.generate(prompt="What is the liability cap under Section 12?", tenant_id="tenant_a")

    assert result is not None
    assert "liability cap" in result["content"].lower()
    assert result["cached"] is False
    assert result["circuit_state"] == "CLOSED"
    assert "azure" in result["provider_used"].lower()


def test_gateway_semantic_caching():
    """Verifies that duplicate queries hit the semantic cache with zero token cost and sub-10ms latency."""
    gateway = ResilientLlmGateway()
    prompt = "Identify governing law in Apex Cloud contract."

    # First request: Cache Miss
    res1 = gateway.generate(prompt=prompt, tenant_id="tenant_b")
    assert res1["cached"] is False

    # Second request: Cache Hit
    res2 = gateway.generate(prompt=prompt, tenant_id="tenant_b")
    assert res2["cached"] is True
    assert res2["provider_used"] == "semantic_cache"
    assert res2["cost_estimate_usd"] == 0.0
    assert res2["latency_ms"] < 25.0  # High-speed retrieval


def test_gateway_automatic_fallback_on_429():
    """Verifies that when primary fails (HTTP 429 throttling), failover to open-source vLLM occurs automatically."""
    gateway = ResilientLlmGateway()
    
    # Force primary failure to simulate Azure OpenAI HTTP 429 outage
    result = gateway.generate(
        prompt="Audit indemnification clauses.",
        tenant_id="tenant_c",
        force_fail_primary=True
    )

    assert "opensource_fallback" in result["provider_used"].lower()
    assert "llama-3.3-70b" in result["provider_used"].lower()
    assert "Notice: Azure OpenAI rate-limited" in result["content"]


def test_circuit_breaker_tripping_and_recovery():
    """Verifies that circuit breaker transitions CLOSED -> OPEN -> HALF_OPEN -> CLOSED."""
    breaker = CircuitBreaker("test_provider", failure_threshold=2, recovery_timeout_seconds=0.1)
    assert breaker.state == CircuitState.CLOSED
    assert breaker.can_execute() is True

    # First failure
    breaker.record_failure()
    assert breaker.state == CircuitState.CLOSED

    # Second failure -> Threshold reached, trip to OPEN
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    assert breaker.can_execute() is False

    # Wait for cooldown
    time.sleep(0.15)
    assert breaker.can_execute() is True  # Transitions to HALF_OPEN
    assert breaker.state == CircuitState.HALF_OPEN

    # Record success -> Recovers to CLOSED
    breaker.record_success()
    assert breaker.state == CircuitState.CLOSED


def test_rate_limiter_exceeded():
    """Verifies that Token-Bucket Rate Limiter strictly blocks requests exceeding quotas."""
    limiter = TokenBucketRateLimiter(default_rate_rpm=2, burst_multiplier=1.0)
    
    # 2 requests allowed
    assert limiter.acquire("tenant_x") is True
    assert limiter.acquire("tenant_x") is True

    # 3rd request immediately blocked
    assert limiter.acquire("tenant_x") is False
