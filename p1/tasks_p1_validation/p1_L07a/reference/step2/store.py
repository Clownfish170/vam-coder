"""Loan store"""

DATA = {}
LOG = {}


def save_i(k, v):
    DATA[k] = v
    LOG.setdefault(k, []).append(v)
    return DATA


def load_i(k):
    return DATA.get(k)
