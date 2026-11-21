"""Tier computation module"""


def tier_of(v):
    if v < 0:
        return 0
    return v * 7


def plain(v):
    return v


def tier_pair(n):
    return tier_of(n) + plain(n)
