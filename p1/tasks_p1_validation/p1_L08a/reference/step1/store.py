"""Tax store"""

DATA = {}


def put_tax(k, v):
    DATA[k] = v
    return DATA


def get_tax(k):
    return DATA.get(k)
