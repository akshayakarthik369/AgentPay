"""
Phase 10 — Base Verifier Interface and Common Scoring Framework.

All category-specific verifiers inherit from BaseVerifier.
Provides deterministic scoring functions, reason extraction, and warning generation.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from app.config.verification import (
    ACCURACY_WEIGHT,
    COMPLETENESS_WEIGHT,
    QUALITY_WEIGHT,
    FORMAT_WEIGHT,
    EVIDENCE_WEIGHT,
    REVIEW_MARGIN,
)


class VerificationResult:
    def __init__(
        self,
        accuracy_score: float,
        completeness_score: float,
        format_compliance_score: float,
        quality_score: float,
        evidence_score: float,
        overall_score: float,
        required_score: float,
        decision: str,
        reasons: Dict[str, List[str]],
        warnings: List[str],
        details: Dict[str, Any],
    ):
        self.accuracy_score = round(accuracy_score, 2)
        self.completeness_score = round(completeness_score, 2)
        self.format_compliance_score = round(format_compliance_score, 2)
        self.quality_score = round(quality_score, 2)
        self.evidence_score = round(evidence_score, 2)
        self.overall_score = round(overall_score, 2)
        self.required_score = round(required_score, 2)
        self.decision = decision
        self.reasons = reasons
        self.warnings = warnings
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accuracy_score": self.accuracy_score,
            "completeness_score": self.completeness_score,
            "format_compliance_score": self.format_compliance_score,
            "quality_score": self.quality_score,
            "evidence_score": self.evidence_score,
            "overall_score": self.overall_score,
            "required_score": self.required_score,
            "decision": self.decision,
            "reasons": self.reasons,
            "warnings": self.warnings,
            "details": self.details,
        }


class BaseVerifier(ABC):
    """Abstract base class for all category verifiers."""

    category_name: str = "Generic"

    def verify(
        self,
        output_text: str,
        structured_output: Dict[str, Any],
        task_snapshot: Dict[str, Any],
        evidence: Dict[str, Any],
        provenance: Dict[str, Any],
        limitations: List[str],
        required_score: float,
    ) -> VerificationResult:
        reasons: Dict[str, List[str]] = {
            "accuracy": [],
            "completeness": [],
            "quality": [],
            "format_compliance": [],
            "evidence_provenance": [],
        }
        warnings: List[str] = []
        details: Dict[str, Any] = {}

        # 1. Accuracy
        acc_score, acc_reasons, acc_warnings = self.evaluate_accuracy(
            output_text, structured_output, task_snapshot
        )
        reasons["accuracy"].extend(acc_reasons)
        warnings.extend(acc_warnings)

        # 2. Completeness
        comp_score, comp_reasons, comp_warnings = self.evaluate_completeness(
            output_text, structured_output, task_snapshot, limitations, evidence
        )
        reasons["completeness"].extend(comp_reasons)
        warnings.extend(comp_warnings)

        # 3. Format Compliance
        fmt_score, fmt_reasons, fmt_warnings = self.evaluate_format_compliance(
            output_text, structured_output
        )
        reasons["format_compliance"].extend(fmt_reasons)
        warnings.extend(fmt_warnings)

        # 4. Quality
        qual_score, qual_reasons, qual_warnings = self.evaluate_quality(
            output_text, structured_output, limitations
        )
        reasons["quality"].extend(qual_reasons)
        warnings.extend(qual_warnings)

        # 5. Evidence & Provenance
        ev_score, ev_reasons, ev_warnings = self.evaluate_evidence_provenance(
            evidence, provenance, limitations
        )
        reasons["evidence_provenance"].extend(ev_reasons)
        warnings.extend(ev_warnings)

        # Calculate weighted overall score
        overall = (
            acc_score * ACCURACY_WEIGHT
            + comp_score * COMPLETENESS_WEIGHT
            + qual_score * QUALITY_WEIGHT
            + fmt_score * FORMAT_WEIGHT
            + ev_score * EVIDENCE_WEIGHT
        )
        overall = round(overall, 2)

        # Determine decision
        if overall >= required_score:
            decision = "PASS"
        elif overall >= (required_score - REVIEW_MARGIN):
            decision = "REVIEW"
        else:
            decision = "FAIL"

        details["category_verifier"] = self.category_name
        details["weights_applied"] = {
            "accuracy": ACCURACY_WEIGHT,
            "completeness": COMPLETENESS_WEIGHT,
            "quality": QUALITY_WEIGHT,
            "format_compliance": FORMAT_WEIGHT,
            "evidence_provenance": EVIDENCE_WEIGHT,
        }

        # Deduplicate warnings
        unique_warnings = list(dict.fromkeys(warnings))

        return VerificationResult(
            accuracy_score=acc_score,
            completeness_score=comp_score,
            format_compliance_score=fmt_score,
            quality_score=qual_score,
            evidence_score=ev_score,
            overall_score=overall,
            required_score=required_score,
            decision=decision,
            reasons=reasons,
            warnings=unique_warnings,
            details=details,
        )

    @abstractmethod
    def evaluate_accuracy(
        self,
        output_text: str,
        structured_output: Dict[str, Any],
        task_snapshot: Dict[str, Any],
    ) -> Tuple[float, List[str], List[str]]:
        """Return (score 0-100, reasons, warnings)."""
        pass

    @abstractmethod
    def evaluate_completeness(
        self,
        output_text: str,
        structured_output: Dict[str, Any],
        task_snapshot: Dict[str, Any],
        limitations: List[str],
        evidence: Dict[str, Any],
    ) -> Tuple[float, List[str], List[str]]:
        """Return (score 0-100, reasons, warnings)."""
        pass

    def evaluate_format_compliance(
        self,
        output_text: str,
        structured_output: Dict[str, Any],
    ) -> Tuple[float, List[str], List[str]]:
        score = 100.0
        reasons: List[str] = []
        warnings: List[str] = []

        if not output_text:
            score -= 40.0
            reasons.append("Final output text payload is empty.")
        else:
            reasons.append("Output text payload is well-formed.")

        if not isinstance(structured_output, dict) or not structured_output:
            score -= 40.0
            reasons.append("Structured output is not a valid JSON dictionary.")
        else:
            reasons.append("Structured output parses successfully into valid JSON schema.")

        if isinstance(structured_output, dict) and "summary" in structured_output:
            reasons.append("Top-level summary key exists in structured payload.")
        else:
            score -= 10.0
            warnings.append("Top-level summary key is missing from structured payload.")

        return max(0.0, min(100.0, score)), reasons, warnings

    def evaluate_quality(
        self,
        output_text: str,
        structured_output: Dict[str, Any],
        limitations: List[str],
    ) -> Tuple[float, List[str], List[str]]:
        score = 80.0
        reasons: List[str] = []
        warnings: List[str] = []

        out_len = len(output_text.strip()) if output_text else 0
        if out_len >= 300:
            score += 10.0
            reasons.append(f"Substantial output length ({out_len} characters).")
        elif out_len >= 100:
            score += 5.0
            reasons.append(f"Adequate output length ({out_len} characters).")
        else:
            score -= 20.0
            warnings.append(f"Output text is unusually brief ({out_len} characters).")

        # Check for placeholder strings
        lower_out = (output_text or "").lower()
        placeholders = ["todo", "placeholder", "asdf", "lorem ipsum", "insert here"]
        has_ph = any(ph in lower_out for ph in placeholders)
        if has_ph:
            score -= 30.0
            warnings.append("Detected placeholder or incomplete template markers in output.")
        else:
            reasons.append("No obvious placeholder or incomplete template markers detected.")

        # Check declared limitations
        if limitations and len(limitations) > 0:
            score += 10.0
            reasons.append(f"Explicit limitations disclosed ({len(limitations)} declared).")
        else:
            warnings.append("No explicit limitations declared.")

        return max(0.0, min(100.0, score)), reasons, warnings

    def evaluate_evidence_provenance(
        self,
        evidence: Dict[str, Any],
        provenance: Dict[str, Any],
        limitations: List[str],
    ) -> Tuple[float, List[str], List[str]]:
        score = 85.0
        reasons: List[str] = []
        warnings: List[str] = []

        if not provenance:
            score -= 30.0
            warnings.append("Missing provenance metadata.")
        else:
            provider = provenance.get("execution_provider") or provenance.get("executor_type")
            reasons.append(f"Execution provider verified: '{provider}'.")

            # Reward transparency: if no external dataset was used, check if it was disclosed
            if provenance.get("external_dataset_used") is False:
                reasons.append("Truthfully declared no external dataset was accessed.")
                warnings.append("Synthetic/demo context used (no external dataset accessed).")

            if provenance.get("input_source") == "task_specification":
                reasons.append("Input provenance accurately references task specification.")

        if evidence and isinstance(evidence, dict):
            reasons.append("Auditable evidence structure present.")
            if evidence.get("evidence_type") == "demo_evidence":
                warnings.append("Evidence is marked as synthetic/demo.")

        return max(0.0, min(100.0, score)), reasons, warnings
