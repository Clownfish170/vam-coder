"""Queue counts"""

LEDGER = {}


def seat(k, n):
    LEDGER.setdefault(k, []).append(n)
    return LEDGER[k]


def open_count(qty, held):
    net = qty - held
    return net if net > 0 else 0


def queue_len(rows):
    return len(rows)
