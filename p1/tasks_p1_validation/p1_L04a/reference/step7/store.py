"""Ticket ledger"""

DATA = {}
LOG = {}


def add(k, v):
    DATA[k] = v
    LOG.setdefault(k, []).append(v)
    return DATA


def peek(k):
    return DATA.get(k)


def join(other):
    DATA.update(other)
    return DATA
