"""
Bidding & Agent Selection Configuration for AgentPay.
Defines weights for bid ranking, minimum suitability thresholds, and scoring functions.
"""

# ---------------------------------------------------------------------------
# Bid Selection Factor Weights (Must sum exactly to 1.0)
# ---------------------------------------------------------------------------
MATCH_WEIGHT = 0.45
REPUTATION_WEIGHT = 0.20
PRICE_WEIGHT = 0.20
SPEED_WEIGHT = 0.15

_TOTAL_WEIGHTS = MATCH_WEIGHT + REPUTATION_WEIGHT + PRICE_WEIGHT + SPEED_WEIGHT
assert abs(_TOTAL_WEIGHTS - 1.0) < 1e-6, f"Bidding weights must sum to 1.0, got {_TOTAL_WEIGHTS}"

# ---------------------------------------------------------------------------
# Minimum Match Threshold to Submit a Bid
# ---------------------------------------------------------------------------
MIN_BID_MATCH_SCORE = 60.0


def calculate_price_score(bid_amount: float, task_reward: float) -> float:
    """
    Calculate price competitiveness score (0 to 100).
    Rewards reasonable discounts while moderating extreme / unrealistically low bids.
    """
    if task_reward <= 0 or bid_amount <= 0:
        return 50.0

    ratio = bid_amount / task_reward

    if ratio > 1.0:
        # Over budget
        return 0.0
    elif ratio <= 0.60:
        # Generous discount (40%+ off)
        return 95.0
    elif ratio <= 0.75:
        # Strong discount (25-40% off)
        return 100.0
    elif ratio <= 0.85:
        # Competitive discount (15-25% off)
        return 90.0
    elif ratio <= 0.95:
        # Slight discount (5-15% off)
        return 80.0
    else:
        # Near full reward (0-5% off)
        return 70.0


def calculate_speed_score(estimated_minutes: int) -> float:
    """
    Calculate completion speed score (0 to 100) based on estimated minutes.
    """
    if estimated_minutes <= 0:
        return 50.0
    elif estimated_minutes <= 30:
        return 100.0
    elif estimated_minutes <= 60:
        return 90.0
    elif estimated_minutes <= 120:
        return 75.0
    elif estimated_minutes <= 240:
        return 60.0
    else:
        return 40.0


def calculate_bid_selection_score(
    match_score: float,
    reputation: float,
    bid_amount: float,
    task_reward: float,
    estimated_minutes: int,
) -> float:
    """
    Calculate deterministic overall selection score (0 to 100) for a bid.
    """
    price_score = calculate_price_score(bid_amount, task_reward)
    speed_score = calculate_speed_score(estimated_minutes)

    overall = (
        (match_score * MATCH_WEIGHT)
        + (reputation * REPUTATION_WEIGHT)
        + (price_score * PRICE_WEIGHT)
        + (speed_score * SPEED_WEIGHT)
    )

    return round(max(0.0, min(100.0, overall)), 1)
