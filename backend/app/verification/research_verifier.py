"""
Phase 10 — Research & Investigation Category Verifier.
"""
from typing import Any, Dict, List, Tuple
from .base_verifier import BaseVerifier


class ResearchVerifier(BaseVerifier):
    category_name = "Research & Investigation"

    def evaluate_accuracy(
        self,
        output_text: str,
        structured_output: Dict[str, Any],
        task_snapshot: Dict[str, Any],
    ) -> Tuple[float, List[str], List[str]]:
        score = 85.0
        reasons: List[str] = []
        warnings: List[str] = []

        lower_out = (output_text or "").lower()

        # Check findings in structured output
        findings = structured_output.get("findings")
        if isinstance(findings, list) and len(findings) >= 2:
            score += 10.0
            reasons.append(f"Structured research findings present ({len(findings)} distinct findings).")
        elif isinstance(findings, list) and len(findings) >= 1:
            score += 5.0
            reasons.append("Structured research findings present.")
        else:
            score -= 15.0
            warnings.append("Research output lacks structured findings list.")

        # Check methodology or research structure
        if "methodology" in structured_output or "scope" in structured_output or "themes" in structured_output:
            score += 5.0
            reasons.append("Research methodology/thematic framework explicitly articulated.")

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
            reasons.append("Executive research summary is documented.")
        else:
            score -= 10.0
            warnings.append("Executive research summary is missing.")

        if limitations and len(limitations) > 0:
            score += 10.0
            reasons.append("Investigation limitations and boundary conditions declared.")
        else:
            warnings.append("No research limitations or boundary conditions provided.")

        return max(0.0, min(100.0, score)), reasons, warnings
