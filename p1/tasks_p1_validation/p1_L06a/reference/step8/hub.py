"""Rent hub"""
from policy import LIMIT


def fee_of(qty):
    if qty < 0:
        return 0
    return qty * 3


def scrub(x):
    if x is None:
        return "-"
    return x


def cap_rent(fee):
    return fee if fee <= LIMIT else LIMIT
