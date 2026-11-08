"""Quote arithmetic"""
from rates import RATE


def apply_rate(v):
    return v + RATE


def positive(v):
    return v > 0
