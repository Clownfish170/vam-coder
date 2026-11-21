"""Inventory ledger"""

LEDGER = {}


def reserve(k, n):
    LEDGER.setdefault(k, []).append(n)
    return LEDGER[k]


def available(qty, held):
    return qty - held


def count_rows(rows):
    return len(rows)
