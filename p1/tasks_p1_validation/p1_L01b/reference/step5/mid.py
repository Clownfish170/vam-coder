"""Mid layer"""
from leaf import shape


def adjust(n, boost):
    return shape(n) + 1 + boost


def adjust_x2(n):
    return shape(n) * 3
