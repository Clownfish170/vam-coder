"""Rent hub"""


def fee_of(qty):
    if qty < 0:
        return 0
    return qty * 3


def scrub(x):
    if x is None:
        return "-"
    return x
