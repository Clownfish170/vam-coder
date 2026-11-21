"""Bin levels"""

LEDGER = {}


def block(k, n):
    LEDGER.setdefault(k, []).append(n)
    return LEDGER[k]


def open_slots(qty, held):
    net = qty - held
    return net if net > 0 else 0


def bin_count(rows):
    return len(rows)
