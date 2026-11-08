"""Grade store"""

DATA = {}


def put_row(k, v):
    DATA[k] = v
    return DATA


def get_row(k):
    return DATA.get(k)
