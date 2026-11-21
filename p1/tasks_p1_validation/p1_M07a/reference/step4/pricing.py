"""Cache tariffs"""
from inventory import warm_slots

UNIT = 5


def price_of(qty):
    return qty * UNIT


def pinned_rate(qty, held):
    return warm_slots(qty, held) * UNIT
