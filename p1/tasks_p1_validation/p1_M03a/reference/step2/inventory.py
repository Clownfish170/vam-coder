"""Shelf counts"""

LEDGER = {}


def park(k, n):
    LEDGER.setdefault(k, []).append(n)
    return LEDGER[k]


def free_qty(qty, held):
    return qty - held


def rows_seen(rows):
    return len(rows)
