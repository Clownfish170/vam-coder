"""Queue fees"""
from inventory import open_count

UNIT = 12


def price_of(qty):
    return qty * UNIT


def seated_fee(qty, held):
    return open_count(qty, held) * UNIT
