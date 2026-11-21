"""Loan hub"""
from policy import LIMIT


def interest(qty):
    if qty < 0:
        return 0
    return qty * 2


def tidy_i(x):
    if x is None:
        return "-"
    return x


def cap_interest(fee):
    return fee if fee <= LIMIT else LIMIT
