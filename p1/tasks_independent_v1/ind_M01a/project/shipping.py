"""Shipping quotes."""

BASE_RATE = 8
FREE_AT = 500


def weight_fee(weight):
    if weight <= 4:
        return BASE_RATE
    return BASE_RATE + (weight - 4) * 3


def surcharge(subtotal, pct):
    return subtotal * pct


def quote(subtotal, weight, pct):
    return weight_fee(weight) + surcharge(subtotal, pct)
