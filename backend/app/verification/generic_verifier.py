"""
Phase 10 — Generic Fallback Verifier & Verifier Factory.
"""
from typing import Any, Dict, List, Tuple
from .base_verifier import BaseVerifier, VerificationResult
from .nlp_verifier import NLPVerifier
from .research_verifier import ResearchVerifier
from .data_verifier import DataAnalysisVerifier
from .code_verifier import CodeAnalysisVerifier
from .content_verifier import ContentCreationVerifier


class GenericVerifier(BaseVerifier):
    category_name = "Generic Verification"

    def evaluate_accuracy(
        self,
        output_text: str,
        structured_output: Dict[str, Any],
        task_snapshot: Dict[str, Any],
    ) -> Tuple[float, List[str], List[str]]:
        score = 80.0
        reasons: List[str] = []
        warnings: List[str] = []

        if output_text and len(output_text.strip()) > 50:
            score += 10.0
            reasons.append("Output directly responds to task objective.")
        else:
            score -= 10.0
            warnings.append("Output response is minimal.")

        if structured_output and len(structured_output) > 0:
            score += 5.0
            reasons.append("Structured metadata parsed.")

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
            reasons.append("Summary present in structured output.")
        else:
            warnings.append("No explicit summary section in structured output.")

        if limitations and len(limitations) > 0:
            score += 10.0
            reasons.append("Limitations declared.")

        return max(0.0, min(100.0, score)), reasons, warnings


def get_verifier_for_category(category: str) -> BaseVerifier:
    """Factory: return category-specific verifier or Generic fallback."""
    cat_lower = (category or "").lower()
    if "nlp" in cat_lower or "sentiment" in cat_lower or "language" in cat_lower:
        return NLPVerifier()
    elif "research" in cat_lower or "investigat" in cat_lower:
        return ResearchVerifier()
    elif "data" in cat_lower or "analys" in cat_lower or "metric" in cat_lower:
        return DataAnalysisVerifier()
    elif "code" in cat_lower or "review" in cat_lower or "software" in cat_lower or "develop" in cat_lower:
        return CodeAnalysisVerifier()
    elif "content" in cat_lower or "writ" in cat_lower or "copy" in cat_lower or "blog" in cat_lower:
        return ContentCreationVerifier()
    else:
        return GenericVerifier()
