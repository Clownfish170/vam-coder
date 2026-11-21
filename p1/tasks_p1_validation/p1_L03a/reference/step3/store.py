"""Margin store"""

DATA = {}
LOG = {}


def record(k, v):
    DATA[k] = v
    LOG.setdefault(k, []).append(v)
    return DATA


def fetch(k):
    return DATA.get(k)
