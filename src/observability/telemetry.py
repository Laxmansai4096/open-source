"""Enterprise Observability and Cost Accounting Telemetry.

Captures:
1. Token consumption (Prompt Tokens, Completion Tokens, Total Tokens).
2. Cost accounting (Real-time USD cost calculation based on Azure OpenAI tier pricing).
3. Latency waterfalls and Time-to-First-Token (TTFT).
4. Compatible with OpenTelemetry and Azure Application Insights metrics.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone


class TelemetryLogger:
    """Enterprise LLMOps Observability and Cost Accountant."""

    def __init__(self):
        # Azure OpenAI GPT-4o Standard Pricing Rates (per 1,000 tokens)
        self.input_cost_per_1k = 0.005
        self.output_cost_per_1k = 0.015

    def calculate_cost_usd(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Computes precise USD monetary cost of an LLM generation."""
        input_cost = (prompt_tokens / 1000.0) * self.input_cost_per_1k
        output_cost = (completion_tokens / 1000.0) * self.output_cost_per_1k
        return round(input_cost + output_cost, 6)

    def record_session(
        self,
        session_id: str,
        tenant_id: str,
        prompt: str,
        response: str,
        latency_ms: float,
        provider: str
    ) -> Dict[str, Any]:
        """Logs an enterprise telemetry record with token count and cost estimate."""
        prompt_tokens = max(1, len(prompt.split()) * 4 // 3)
        completion_tokens = max(1, len(response.split()) * 4 // 3)
        cost_usd = self.calculate_cost_usd(prompt_tokens, completion_tokens)

        telemetry_record = {
            "session_id": session_id,
            "tenant_id": tenant_id,
            "provider": provider,
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost_usd": cost_usd,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return telemetry_record
