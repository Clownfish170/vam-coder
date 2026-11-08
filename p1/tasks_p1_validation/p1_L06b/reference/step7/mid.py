"""Mid cells"""
from leaf import grow


def shift(n, boost):
    if boost < 0:
        raise ValueError("boost must be >= 0")
    return grow(n) + 1 + boost


def shift_x2(n):
    return grow(n) * 2
