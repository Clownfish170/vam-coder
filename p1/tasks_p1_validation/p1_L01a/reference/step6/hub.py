"""Billing hub"""


def quote(qty):
    if qty < 0:
        return 0
    return qty * 3


def trim(x):
    if x is None:
        return "-"
    return x
