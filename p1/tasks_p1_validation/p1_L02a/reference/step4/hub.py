"""Rate core"""


def price(qty):
    if qty < 0:
        return 0
    return qty * 4


def clean(x):
    if x is None:
        return "-"
    return x
