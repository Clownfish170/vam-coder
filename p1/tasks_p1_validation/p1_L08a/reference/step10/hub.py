"""Tax hub"""
from policy import LIMIT


def compute(qty):
    if qty < 0:
        return 0
    return qty * 4


def fix_tax(x):
    if x is None:
        return "-"
    return x


def cap_tax(fee):
    if fee < 0:
        return 0
    return fee if fee <= LIMIT else LIMIT
