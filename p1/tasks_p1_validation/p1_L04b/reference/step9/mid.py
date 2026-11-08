"""Mid rows"""
from leaf import pad


def align(n, boost):
    if boost < 0:
        raise ValueError("boost must be >= 0")
    return pad(n) + 1 + boost


def align_x2(n):
    return pad(n) * 2
