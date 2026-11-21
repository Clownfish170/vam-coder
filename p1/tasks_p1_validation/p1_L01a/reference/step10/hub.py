"""Billing hub"""
from policy import LIMIT


def quote(qty):
    if qty < 0:
        return 0
    return qty * 3


def trim(x):
    if x is None:
        return "-"
    return x


def cap_fee(fee):
    if fee < 0:
        return 0
    return fee if fee <= LIMIT else LIMIT
