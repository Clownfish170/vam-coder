"""Ticket ledger"""

DATA = {}


def add(k, v):
    DATA[k] = v
    return DATA


def peek(k):
    return DATA.get(k)
