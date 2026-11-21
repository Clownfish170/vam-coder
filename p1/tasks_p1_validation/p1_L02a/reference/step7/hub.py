"""Rate core"""
from policy import LIMIT


def price(qty):
    if qty < 0:
        return 0
    return qty * 4


def clean(x):
    if x is None:
        return "-"
    return x


def apply_cap(fee):
    return fee if fee <= LIMIT else LIMIT
