"""Loan hub"""


def interest(qty):
    if qty < 0:
        return 0
    return qty * 2


def tidy_i(x):
    if x is None:
        return "-"
    return x
