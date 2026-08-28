"""
Matching Engine Configuration & Constants for AgentPay.
Centralizes all factor weights, thresholds, baseline constants, and capability relationship maps.
"""

# ---------------------------------------------------------------------------
# Scoring Factor Weights (Must sum exactly to 1.0)
# ---------------------------------------------------------------------------
CAPABILITY_WEIGHT = 0.50
REPUTATION_WEIGHT = 0.20
QUALITY_WEIGHT = 0.15
SUCCESS_WEIGHT = 0.10
AVAILABILITY_WEIGHT = 0.05

_TOTAL_WEIGHTS = CAPABILITY_WEIGHT + REPUTATION_WEIGHT + QUALITY_WEIGHT + SUCCESS_WEIGHT + AVAILABILITY_WEIGHT
assert abs(_TOTAL_WEIGHTS - 1.0) < 1e-6, f"Matching weights must sum to 1.0, got {_TOTAL_WEIGHTS}"

# ---------------------------------------------------------------------------
# Capability Scoring Constants
# ---------------------------------------------------------------------------
EXACT_CAPABILITY_SCORE = 100.0
RELATED_CAPABILITY_SCORE = 70.0
NO_CAPABILITY_SCORE = 0.0

# ---------------------------------------------------------------------------
# Starter / Neutral Baselines for Agents with 0 Task History
# ---------------------------------------------------------------------------
DEFAULT_NEW_AGENT_QUALITY = 70.0
DEFAULT_NEW_AGENT_SUCCESS_RATE = 70.0

# ---------------------------------------------------------------------------
# Match Level Thresholds
# ---------------------------------------------------------------------------
MATCH_LEVEL_THRESHOLDS = [
    (90.0, "excellent"),
    (75.0, "strong"),
    (60.0, "moderate"),
    (40.0, "weak"),
    (0.0, "poor"),
]

def get_match_level(score: float) -> str:
    """Return descriptive match level based on overall score."""
    for threshold, level in MATCH_LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return "poor"

# ---------------------------------------------------------------------------
# Deterministic Capability Relationship Map (Manual & Explainable)
# Key: normalized primary capability -> Set of normalized related capabilities
# ---------------------------------------------------------------------------
CAPABILITY_RELATIONSHIP_MAP = {
    "nlp": {
        "sentiment analysis",
        "summarization",
        "classification",
        "text analysis",
        "content generation",
        "translation",
        "entity extraction",
        "research",
    },
    "sentiment analysis": {
        "nlp",
        "text analysis",
        "classification",
        "data analysis",
    },
    "summarization": {
        "nlp",
        "research",
        "content generation",
        "text analysis",
    },
    "data analysis": {
        "classification",
        "statistical analysis",
        "forecasting",
        "anomaly detection",
        "sentiment analysis",
    },
    "classification": {
        "nlp",
        "data analysis",
        "sentiment analysis",
    },
    "code analysis": {
        "code review",
        "bug detection",
        "security audit",
        "static analysis",
        "testing",
    },
    "research": {
        "summarization",
        "literature search",
        "synthesis",
        "nlp",
        "data analysis",
    },
    "verification": {
        "quality evaluation",
        "fact checking",
        "compliance audit",
        "code review",
        "security audit",
    },
    "quality evaluation": {
        "verification",
        "compliance audit",
        "fact checking",
    },
}
