"""Pricing."""


def apply_discount(price, pct):
    if pct < 0:
        pct = 0
    if pct > 100:
        pct = 100
    return price - price * (pct / 100.0)
