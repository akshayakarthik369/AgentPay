"""
Phase 10 — Verification Engine Configuration.

Centralizes weights, decision policy thresholds, and criteria definitions.
"""
from typing import Dict

# ── 5 Criteria Weights (Must sum to 1.0) ──────────────────────────────────────
ACCURACY_WEIGHT: float = 0.30
COMPLETENESS_WEIGHT: float = 0.25
QUALITY_WEIGHT: float = 0.20
FORMAT_WEIGHT: float = 0.15
EVIDENCE_WEIGHT: float = 0.10

CRITERIA_WEIGHTS: Dict[str, float] = {
    "accuracy": ACCURACY_WEIGHT,
    "completeness": COMPLETENESS_WEIGHT,
    "quality": QUALITY_WEIGHT,
    "format_compliance": FORMAT_WEIGHT,
    "evidence_provenance": EVIDENCE_WEIGHT,
}

# Runtime assertion: weights must sum to exactly 1.0
assert abs(sum(CRITERIA_WEIGHTS.values()) - 1.0) < 1e-6, "Criteria weights must sum to 1.0"

# ── Decision Policy Thresholds ────────────────────────────────────────────────
# If overall_score is within REVIEW_MARGIN points below required_score -> REVIEW
REVIEW_MARGIN: float = 10.0

# Verifier Suitability Weights for Deterministic Selection
VERIFIER_CAPABILITY_WEIGHT: float = 0.40
VERIFIER_REPUTATION_WEIGHT: float = 0.35
VERIFIER_AVAILABILITY_WEIGHT: float = 0.25
