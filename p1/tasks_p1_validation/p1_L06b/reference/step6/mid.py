"""Mid cells"""
from leaf import grow


def shift(n, boost):
    return grow(n) + 1 + boost


def shift_x2(n):
    return grow(n) * 2
