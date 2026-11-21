"""Bin levels"""

LEDGER = {}


def block(k, n):
    LEDGER.setdefault(k, []).append(n)
    return LEDGER[k]


def open_slots(qty, held):
    return qty - held


def bin_count(rows):
    return len(rows)
