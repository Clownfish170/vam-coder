"""Inventory ledger"""

LEDGER = {}


def reserve(k, n):
    LEDGER.setdefault(k, []).append(n)
    return LEDGER[k]


def available(qty, held):
    net = qty - held
    return net if net > 0 else 0


def count_rows(rows):
    return len(rows)
