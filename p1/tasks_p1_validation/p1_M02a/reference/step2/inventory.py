"""Stock tracking"""

LEDGER = {}


def hold(k, n):
    LEDGER.setdefault(k, []).append(n)
    return LEDGER[k]


def net_of(qty, held):
    return qty - held


def tally(rows):
    return len(rows)
