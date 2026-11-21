"""Rate log"""

DATA = {}


def save(k, v):
    DATA[k] = v
    return DATA


def load(k):
    return DATA.get(k)
