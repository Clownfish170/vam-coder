"""Invoice helpers."""

from shipping import quote


def order_total(subtotal, weight, pct):
    return quote(subtotal, weight, pct)
