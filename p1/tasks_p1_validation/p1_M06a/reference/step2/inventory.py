"""Queue counts"""

LEDGER = {}


def seat(k, n):
    LEDGER.setdefault(k, []).append(n)
    return LEDGER[k]


def open_count(qty, held):
    return qty - held


def queue_len(rows):
    return len(rows)
