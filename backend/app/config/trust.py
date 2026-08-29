"""
app/config/trust.py — Centralized Trust & Canary Configuration for AgentPay Phase 21.

All trust-related thresholds and limits are defined here.
Do NOT hardcode these values in services or routers.
"""

# ── Canary Test ────────────────────────────────────────────────────────────────
CANARY_REQUIRED_SCORE: int = 80          # Minimum score (0-100) to pass canary
CANARY_MAX_ATTEMPTS: int = 5             # Maximum retest attempts before permanent block

# ── Provisional Agent Limits ───────────────────────────────────────────────────
PROVISIONAL_START_REPUTATION: float = 55.0    # Reputation assigned on canary PASS
PROVISIONAL_MAX_REWARD: float = 200.0          # Max task reward (AP) for provisional agents

# ── Promotion to Trusted Criteria ─────────────────────────────────────────────
TRUSTED_REPUTATION_THRESHOLD: float = 70.0    # Minimum reputation to be promoted
TRUSTED_MIN_VERIFIED_TASKS: int = 3            # Minimum independently verified tasks completed
TRUSTED_MAX_RISK_SCORE: float = 60.0           # Risk score must be below this to promote

# ── Trust Statuses ─────────────────────────────────────────────────────────────
TRUST_STATUS_PENDING_CANARY = "pending_canary"
TRUST_STATUS_CANARY_TESTING = "canary_testing"
TRUST_STATUS_PROVISIONAL = "provisional"
TRUST_STATUS_TRUSTED = "trusted"
TRUST_STATUS_CANARY_FAILED = "canary_failed"
TRUST_STATUS_SUSPENDED = "suspended"

# Statuses that prevent ANY real task participation
TRUST_BLOCKED_STATUSES = {
    TRUST_STATUS_PENDING_CANARY,
    TRUST_STATUS_CANARY_TESTING,
    TRUST_STATUS_CANARY_FAILED,
}

# Human-readable labels for UI display
TRUST_STATUS_LABELS = {
    TRUST_STATUS_PENDING_CANARY: "Canary Required",
    TRUST_STATUS_CANARY_TESTING: "Canary Testing",
    TRUST_STATUS_PROVISIONAL: "Provisional",
    TRUST_STATUS_TRUSTED: "Trusted",
    TRUST_STATUS_CANARY_FAILED: "Canary Failed",
    TRUST_STATUS_SUSPENDED: "Suspended",
}
