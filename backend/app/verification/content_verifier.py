"""
Phase 10 — Content Creation & Writing Category Verifier.
"""
from typing import Any, Dict, List, Tuple
from .base_verifier import BaseVerifier


class ContentCreationVerifier(BaseVerifier):
    category_name = "Content Creation"

    def evaluate_accuracy(
        self,
        output_text: str,
        structured_output: Dict[str, Any],
        task_snapshot: Dict[str, Any],
    ) -> Tuple[float, List[str], List[str]]:
        score = 85.0
        reasons: List[str] = []
        warnings: List[str] = []

        # Check sections in structured output
        sections = structured_output.get("sections")
        if isinstance(sections, list) and len(sections) >= 2:
            score += 10.0
            reasons.append(f"Structured content sections generated ({len(sections)} sections).")
        elif isinstance(sections, list) and len(sections) >= 1:
            score += 5.0
            reasons.append("Structured content section generated.")
        else:
            score -= 10.0
            warnings.append("Content lacks structured sections list.")

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

        if "summary" in structured_output or "brief" in structured_output:
            score += 10.0
            reasons.append("Content brief/summary section present.")
        else:
            score -= 10.0
            warnings.append("Content brief/summary section is missing.")

        if output_text and len(output_text.split()) >= 40:
            score += 10.0
            reasons.append("Word count meets depth criteria.")
        else:
            warnings.append("Generated content is concise.")

        return max(0.0, min(100.0, score)), reasons, warnings
