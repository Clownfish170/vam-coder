"""Mid units"""
from leaf import norm


def tune(n, boost):
    if boost < 0:
        raise ValueError("boost must be >= 0")
    return norm(n) + 1 + boost


def tune_x2(n):
    return norm(n) * 4
