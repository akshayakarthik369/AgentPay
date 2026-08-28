"""
Phase 10 — Code Analysis & Review Category Verifier.
"""
from typing import Any, Dict, List, Tuple
from .base_verifier import BaseVerifier


class CodeAnalysisVerifier(BaseVerifier):
    category_name = "Code Review & Analysis"

    def evaluate_accuracy(
        self,
        output_text: str,
        structured_output: Dict[str, Any],
        task_snapshot: Dict[str, Any],
    ) -> Tuple[float, List[str], List[str]]:
        score = 85.0
        reasons: List[str] = []
        warnings: List[str] = []

        # Check issues list
        issues = structured_output.get("issues")
        if isinstance(issues, list) and len(issues) >= 1:
            score += 10.0
            reasons.append(f"Identified structured code issues ({len(issues)} items).")
        else:
            score -= 10.0
            warnings.append("No structured code issues list provided.")

        # Check recommendations
        if "recommendations" in structured_output or "refactorings" in structured_output:
            score += 5.0
            reasons.append("Code improvement recommendations present.")

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
            reasons.append("Code review summary section present.")
        else:
            score -= 10.0
            warnings.append("Code review summary section is missing.")

        if "quality_score" in structured_output or "score" in structured_output:
            score += 10.0
            reasons.append("Internal code quality evaluation score provided.")

        return max(0.0, min(100.0, score)), reasons, warnings
