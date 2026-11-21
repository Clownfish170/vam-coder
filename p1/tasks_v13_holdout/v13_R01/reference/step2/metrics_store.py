"""Metric point storage."""

DATA = {}
HISTORY = {}


def put(k, v):
    DATA[k] = v
    HISTORY.setdefault(k, []).append(v)
    return DATA


def get(k):
    return DATA.get(k)
