"""Mid layer"""
from leaf import shape


def adjust(n, boost):
    if boost < 0:
        raise ValueError("boost must be >= 0")
    return shape(n) + 1 + boost


def adjust_x2(n):
    return shape(n) * 3
