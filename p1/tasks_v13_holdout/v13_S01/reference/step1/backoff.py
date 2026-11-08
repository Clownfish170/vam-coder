"""Retry backoff helpers."""


def delay(base, attempt):
    """Exponential delay in seconds."""
    if attempt >= 5:
        return 30
    return base * (2 ** attempt)


def full_delay(base, attempt):
    d = delay(base, attempt)
    return min(d, 120)
