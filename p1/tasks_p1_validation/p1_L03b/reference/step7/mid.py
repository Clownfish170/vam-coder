"""Mid tokens"""
from leaf import embed


def bias(n, boost):
    if boost < 0:
        raise ValueError("boost must be >= 0")
    return embed(n) + 1 + boost


def bias_x2(n):
    return embed(n) * 5
