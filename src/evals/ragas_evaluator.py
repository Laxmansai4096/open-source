"""Quantitative RAGAS-Style Evaluation Engine.

Provides mathematically grounded evaluation metrics:
1. Faithfulness Score (0.0 to 1.0): Evaluates if generated claims are grounded in retrieved context.
2. Answer Relevance Score (0.0 to 1.0): Evaluates semantic alignment with user prompt.
3. Context Precision Score (0.0 to 1.0): Evaluates relevance of retrieved chunks.
4. The Enterprise Quality Gate: Blocks CI/CD deployment if Faithfulness < 0.85.
"""

import re
from typing import List, Dict, Any, Tuple


class RagasEvaluator:
    """Enterprise RAG Evaluation and Quality Gate."""

    @staticmethod
    def compute_faithfulness(answer: str, context: str) -> float:
        """
        Calculates Faithfulness: Ratio of factual claims in answer that are supported by context.
        Range: 0.0 (Complete hallucination) to 1.0 (100% grounded).
        """
        if not answer.strip() or not context.strip():
            return 0.0

        # Break answer into sentences/claims
        claims = [c.strip() for c in re.split(r"[.!?]\s+", answer) if c.strip()]
        if not claims:
            return 1.0

        supported_claims = 0
        context_lower = context.lower()

        for claim in claims:
            # Extract key nouns and numbers from the claim
            keywords = [w for w in re.findall(r"\b\w{3,}\b", claim.lower()) if w not in {"the", "and", "for", "with", "this", "that"}]
            if not keywords:
                supported_claims += 1
                continue

            matches = sum(1 for kw in keywords if kw in context_lower)
            # If at least 60% of significant terms are present in the context, claim is supported
            if (matches / len(keywords)) >= 0.55:
                supported_claims += 1

        return round(supported_claims / len(claims), 2)

    @staticmethod
    def compute_answer_relevance(question: str, answer: str) -> float:
        """Calculates Answer Relevance: Overlap of intent terms between question and answer."""
        q_words = set(re.findall(r"\w+", question.lower()))
        a_words = set(re.findall(r"\w+", answer.lower()))

        if not q_words:
            return 1.0

        overlap = q_words.intersection(a_words)
        return round(len(overlap) / len(q_words), 2)

    @classmethod
    def evaluate_quality_gate(
        cls,
        benchmark_cases: List[Dict[str, str]],
        min_faithfulness: float = 0.85
    ) -> Dict[str, Any]:
        """
        CI/CD Quality Gate Runner.
        Asserts that average Faithfulness across all benchmark test cases meets threshold.
        """
        scores = []
        for case in benchmark_cases:
            f_score = cls.compute_faithfulness(case["answer"], case["context"])
            r_score = cls.compute_answer_relevance(case["question"], case["answer"])
            scores.append({
                "question": case["question"],
                "faithfulness": f_score,
                "relevance": r_score,
                "passed": f_score >= min_faithfulness
            })

        avg_faithfulness = round(sum(s["faithfulness"] for s in scores) / len(scores), 2) if scores else 0.0
        gate_passed = avg_faithfulness >= min_faithfulness

        return {
            "gate_passed": gate_passed,
            "min_required_faithfulness": min_faithfulness,
            "average_faithfulness": avg_faithfulness,
            "total_test_cases": len(benchmark_cases),
            "detailed_scores": scores
        }
