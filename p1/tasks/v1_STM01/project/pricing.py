"""Pricing rules."""

UNIT = 10


def price(qty):
    """Unit price is UNIT (=10) per piece."""
    return qty * UNIT
