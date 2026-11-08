"""Cache entries"""

LEDGER = {}


def pin(k, n):
    LEDGER.setdefault(k, []).append(n)
    return LEDGER[k]


def warm_slots(qty, held):
    return qty - held


def entry_no(rows):
    return len(rows)
