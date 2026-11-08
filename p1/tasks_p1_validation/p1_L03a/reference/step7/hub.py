"""Margin hub"""
from policy import LIMIT


def scale(qty):
    if qty < 0:
        return 0
    return qty * 2


def norm(x):
    if x is None:
        return "-"
    return x


def bound(fee):
    return fee if fee <= LIMIT else LIMIT
