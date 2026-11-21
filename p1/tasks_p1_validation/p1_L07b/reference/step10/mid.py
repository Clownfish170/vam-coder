"""Mid stats"""
from leaf import meanish


def amp(n, boost):
    if boost < 0:
        raise ValueError("boost must be >= 0")
    return meanish(n) + 1 + boost


def amp_x2(n):
    return meanish(n) * 6
