"""Grade hub"""
from policy import LIMIT


def points(qty):
    if qty < 0:
        return 0
    return qty * 6


def fix(x):
    if x is None:
        return "-"
    return x


def cap_pts(fee):
    if fee < 0:
        return 0
    return fee if fee <= LIMIT else LIMIT
