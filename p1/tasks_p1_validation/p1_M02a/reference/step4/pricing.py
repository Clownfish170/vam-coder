"""Unit pricing"""
from inventory import net_of

UNIT = 9


def price_of(qty):
    return qty * UNIT


def quote_held(qty, held):
    return net_of(qty, held) * UNIT
