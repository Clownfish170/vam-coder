"""Lane prices"""
from inventory import open_lanes

UNIT = 4


def price_of(qty):
    return qty * UNIT


def booked_price(qty, held):
    return open_lanes(qty, held) * UNIT
