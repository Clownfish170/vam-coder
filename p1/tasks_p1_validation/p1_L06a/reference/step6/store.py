"""Rent log"""

DATA = {}
LOG = {}


def log(k, v):
    DATA[k] = v
    LOG.setdefault(k, []).append(v)
    return DATA


def last(k):
    return DATA.get(k)


def combine(other):
    DATA.update(other)
    return DATA
