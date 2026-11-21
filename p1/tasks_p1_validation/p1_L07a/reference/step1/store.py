"""Loan store"""

DATA = {}


def save_i(k, v):
    DATA[k] = v
    return DATA


def load_i(k):
    return DATA.get(k)
