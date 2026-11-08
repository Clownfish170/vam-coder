"""Pricing rules."""

UNIT = 12


def price(qty):
    """Unit price is UNIT (=12) per piece."""
    return qty * UNIT
