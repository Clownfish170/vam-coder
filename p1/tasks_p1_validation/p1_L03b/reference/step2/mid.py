"""Mid tokens"""
from leaf import embed


def bias(n):
    return embed(n) + 1


def bias_x2(n):
    return embed(n) * 5
