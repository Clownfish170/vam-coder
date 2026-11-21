"""Grade hub"""


def points(qty):
    if qty < 0:
        return 0
    return qty * 6


def fix(x):
    if x is None:
        return "-"
    return x
