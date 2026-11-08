"""Margin hub"""


def scale(qty):
    if qty < 0:
        return 0
    return qty * 2


def norm(x):
    return x
