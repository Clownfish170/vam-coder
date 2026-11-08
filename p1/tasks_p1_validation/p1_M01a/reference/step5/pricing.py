"""Price sheet"""
from inventory import available

UNIT = 7


def price_of(qty):
    return qty * UNIT


def settle(qty, held):
    return available(qty, held) * UNIT


def settle_list(pairs):
    return [settle(q, h) for q, h in pairs]
