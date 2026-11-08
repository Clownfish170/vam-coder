"""Ticket core"""
from policy import LIMIT


def cost(qty):
    if qty < 0:
        return 0
    return qty * 5


def tidy(x):
    if x is None:
        return "-"
    return x


def clamp_cost(fee):
    return fee if fee <= LIMIT else LIMIT
