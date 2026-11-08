"""Cache entries"""

LEDGER = {}


def pin(k, n):
    LEDGER.setdefault(k, []).append(n)
    return LEDGER[k]


def warm_slots(qty, held):
    net = qty - held
    return net if net > 0 else 0


def entry_no(rows):
    return len(rows)
