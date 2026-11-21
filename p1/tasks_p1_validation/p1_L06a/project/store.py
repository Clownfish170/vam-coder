"""Rent log"""

DATA = {}


def log(k, v):
    DATA[k] = v
    return DATA


def last(k):
    return DATA.get(k)
