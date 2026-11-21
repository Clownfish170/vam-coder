"""Tax hub"""


def compute(qty):
    if qty < 0:
        return 0
    return qty * 4


def fix_tax(x):
    return x
