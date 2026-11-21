"""Mid tokens"""
from leaf import embed


def bias(n):
    return embed(n) + 1
