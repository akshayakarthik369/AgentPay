"""
Phase 10 — NLP & Sentiment Category Verifier.
"""
from typing import Any, Dict, List, Tuple
from .base_verifier import BaseVerifier


class NLPVerifier(BaseVerifier):
    category_name = "NLP / Sentiment Analysis"

    def evaluate_accuracy(
        self,
        output_text: str,
        structured_output: Dict[str, Any],
        task_snapshot: Dict[str, Any],
    ) -> Tuple[float, List[str], List[str]]:
        score = 85.0
        reasons: List[str] = []
        warnings: List[str] = []

        title = (task_snapshot.get("title") or "").lower()
        desc = (task_snapshot.get("description") or "").lower()
        lower_out = (output_text or "").lower()

        # Check sentiment fields in structured output
        has_sentiment = (
            "sentiment" in structured_output
            or "sentiment_distribution" in structured_output
            or "overall_sentiment" in structured_output
        )
        if has_sentiment:
            score += 10.0
            reasons.append("Structured sentiment distribution is explicitly calculated.")
        else:
            score -= 15.0
            warnings.append("No explicit sentiment distribution in structured output.")

        # Check themes / keywords
        if "themes" in structured_output or "topics" in structured_output:
            score += 5.0
            reasons.append("Extracted NLP themes and topics match expected schema.")

        # Relevance to task title/description
        nlp_keywords = ["sentiment", "positive", "negative", "neutral", "analysis", "text", "tone", "nlp"]
        matches = [kw for kw in nlp_keywords if kw in lower_out]
        if len(matches) >= 3:
            reasons.append(f"Output vocabulary strongly aligns with NLP objective ({', '.join(matches[:4])}).")
        else:
            score -= 10.0
            warnings.append("Output contains low density of NLP analytical terminology.")

        return max(0.0, min(100.0, score)), reasons, warnings

    def evaluate_completeness(
        self,
        output_text: str,
        structured_output: Dict[str, Any],
        task_snapshot: Dict[str, Any],
        limitations: List[str],
        evidence: Dict[str, Any],
    ) -> Tuple[float, List[str], List[str]]:
        score = 80.0
        reasons: List[str] = []
        warnings: List[str] = []

        if "summary" in structured_output:
            score += 10.0
            reasons.append("Executive summary section present.")
        else:
            score -= 10.0
            warnings.append("Executive summary is missing.")

        if "findings" in structured_output or "key_points" in structured_output:
            score += 10.0
            reasons.append("NLP findings and key insights documented.")

        return max(0.0, min(100.0, score)), reasons, warnings
