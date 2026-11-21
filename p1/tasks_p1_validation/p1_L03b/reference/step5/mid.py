"""Mid tokens"""
from leaf import embed


def bias(n, boost):
    return embed(n) + 1 + boost


def bias_x2(n):
    return embed(n) * 5
