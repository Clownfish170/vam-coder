"""Margin store"""

DATA = {}


def record(k, v):
    DATA[k] = v
    return DATA


def fetch(k):
    return DATA.get(k)
