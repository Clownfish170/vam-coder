"""Shelf counts"""

LEDGER = {}


def park(k, n):
    LEDGER.setdefault(k, []).append(n)
    return LEDGER[k]


def free_qty(qty, held):
    net = qty - held
    return net if net > 0 else 0


def rows_seen(rows):
    return len(rows)
