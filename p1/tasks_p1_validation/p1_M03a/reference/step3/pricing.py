"""Shelf rates"""
from inventory import free_qty

UNIT = 6


def price_of(qty):
    return qty * UNIT


def parked_price(qty, held):
    return free_qty(qty, held) * UNIT
