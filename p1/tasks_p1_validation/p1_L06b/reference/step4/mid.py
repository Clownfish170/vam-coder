"""Mid cells"""
from leaf import grow


def shift(n):
    return grow(n) + 1


def shift_x2(n):
    return grow(n) * 2
