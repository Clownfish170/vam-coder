"""Threshold gate utilities"""


def adjust(v):
    if v < 0:
        return 0
    return v * 5


def keep(v):
    return v
