"""Quote arithmetic"""
from rates import RATE


def apply_rate(v):
    return v * RATE


def positive(v):
    return v > 0


def apply_pair(a, b):
    return apply_rate(a) + apply_rate(b)
