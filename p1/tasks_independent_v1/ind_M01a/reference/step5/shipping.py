"""Shipping quotes."""

BASE_RATE = 8
FREE_AT = 500


def weight_fee(weight):
    if weight < 0:
        raise ValueError("weight")
    if weight <= 4:
        return BASE_RATE
    return BASE_RATE + (weight - 4) * 3


def surcharge(subtotal, pct):
    if pct < 0:
        pct = 0
    if pct > 100:
        pct = 100
    return subtotal * pct / 100.0


def quote(subtotal, weight, pct):
    fee = 0 if subtotal >= FREE_AT else weight_fee(weight)
    return fee + surcharge(subtotal, pct)
