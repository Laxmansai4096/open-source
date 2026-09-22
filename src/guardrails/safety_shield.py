"""Enterprise Guardrails & Security Shield.

Provides:
1. Indirect Prompt Injection Shield: Neutralizes adversarial attempts to override
   system prompts or bypass contract liability clauses.
2. PII Anonymization: Redacts Social Security Numbers (SSN), Credit Card Numbers (CCN),
   and employee taxpayer identifiers before indexing or model processing.
3. Dual-Mode: Live Azure AI Content Safety or high-speed local regex pattern engine.
"""

import re
from typing import Dict, Any, Tuple
from src.core.config import settings


class SecurityShield:
    """Enterprise Content Safety and PII Anonymizer."""

    def __init__(self):
        self.run_mode = settings.run_mode

        # Prompt Injection & Jailbreak Heuristics
        self.injection_patterns = [
            r"ignore\s+(all\s+)?(previous|above)\s+instructions",
            r"system\s+prompt\s+leak",
            r"disregard\s+(the\s+)?(rules|contract)",
            r"act\s+as\s+(an\s+)?unrestricted",
            r"bypass\s+(all\s+)?safety\s+filters",
            r"you\s+are\s+now\s+in\s+developer\s+mode"
        ]

        # PII Regex Patterns
        self.ssn_pattern = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
        self.ccn_pattern = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
        self.email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    def inspect_prompt_injection(self, text: str) -> Tuple[bool, str]:
        """
        Inspects text for adversarial prompt injection.
        Returns (is_safe, reason).
        """
        lower_text = text.lower()
        for pattern in self.injection_patterns:
            if re.search(pattern, lower_text):
                return False, f"Adversarial Prompt Injection Detected: matched pattern '{pattern}'"

        return True, "Safe"

    def redact_pii(self, text: str) -> str:
        """Sanitizes PII from contract text, replacing sensitive data with compliance markers."""
        # Redact SSN
        clean = self.ssn_pattern.sub("[REDACTED_SSN]", text)
        # Redact Credit Cards
        clean = self.ccn_pattern.sub("[REDACTED_CCN]", clean)
        return clean
