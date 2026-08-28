"""
Phase 10 — Data Analysis Category Verifier.
"""
from typing import Any, Dict, List, Tuple
from .base_verifier import BaseVerifier


class DataAnalysisVerifier(BaseVerifier):
    category_name = "Data Analysis"

    def evaluate_accuracy(
        self,
        output_text: str,
        structured_output: Dict[str, Any],
        task_snapshot: Dict[str, Any],
    ) -> Tuple[float, List[str], List[str]]:
        score = 85.0
        reasons: List[str] = []
        warnings: List[str] = []

        # Check key metrics or computed statistics
        metrics = structured_output.get("key_metrics") or structured_output.get("metrics")
        if isinstance(metrics, dict) and len(metrics) >= 2:
            score += 10.0
            reasons.append(f"Quantitative metrics structured and calculated ({', '.join(metrics.keys())}).")
        elif isinstance(metrics, dict) and len(metrics) >= 1:
            score += 5.0
            reasons.append("Quantitative metrics present in structured output.")
        else:
            score -= 15.0
            warnings.append("No quantitative key metrics dictionary in structured output.")

        # Check findings / observations
        observations = structured_output.get("observations") or structured_output.get("findings")
        if isinstance(observations, list) and len(observations) >= 1:
            score += 5.0
            reasons.append("Analytical observations and patterns documented.")

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
            reasons.append("Data analysis summary section present.")
        else:
            score -= 10.0
            warnings.append("Data analysis summary section is missing.")

        if "insights" in structured_output or "findings" in structured_output or "recommendations" in structured_output:
            score += 10.0
            reasons.append("Actionable business/data insights provided.")

        return max(0.0, min(100.0, score)), reasons, warnings
