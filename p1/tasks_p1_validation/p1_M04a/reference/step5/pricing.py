"""Bin charges"""
from inventory import open_slots

UNIT = 8


def price_of(qty):
    return qty * UNIT


def billed(qty, held):
    return open_slots(qty, held) * UNIT


def billed_all(pairs):
    return [billed(q, h) for q, h in pairs]
