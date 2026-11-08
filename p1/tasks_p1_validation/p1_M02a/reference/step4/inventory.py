"""Stock tracking"""

LEDGER = {}


def hold(k, n):
    LEDGER.setdefault(k, []).append(n)
    return LEDGER[k]


def net_of(qty, held):
    net = qty - held
    return net if net > 0 else 0


def tally(rows):
    return len(rows)
