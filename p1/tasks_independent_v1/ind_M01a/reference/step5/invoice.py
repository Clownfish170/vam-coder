"""Invoice helpers."""

from shipping import quote


def order_total(subtotal, weight, pct):
    return quote(subtotal, weight, pct)


def batch_total(rows):
    return sum(order_total(s, w, p) for s, w, p in rows)
