"""Pool meters"""

LEDGER = {}


def dial(k, n):
    LEDGER.setdefault(k, []).append(n)
    return LEDGER[k]


def net_flow(qty, held):
    net = qty - held
    return net if net > 0 else 0


def log_rows(rows):
    return len(rows)
