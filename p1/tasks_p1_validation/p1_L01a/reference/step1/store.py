"""Fee store"""

DATA = {}


def put(k, v):
    DATA[k] = v
    return DATA


def get(k):
    return DATA.get(k)
