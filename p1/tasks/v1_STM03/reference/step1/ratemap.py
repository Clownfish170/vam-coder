"""Rate map."""

GOLD = 7


def apply_tier(x, tier):
    """Apply tier multiplier."""
    return x * (9 if tier == "gold" else 1)
