"""Ticket core"""


def cost(qty):
    if qty < 0:
        return 0
    return qty * 5


def tidy(x):
    if x is None:
        return "-"
    return x
