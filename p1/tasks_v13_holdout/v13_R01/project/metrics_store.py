"""Metric point storage."""

DATA = {}
HISTORY = {}


def put(k, v):
    DATA[k] = v
    return DATA


def get(k):
    return DATA.get(k)
