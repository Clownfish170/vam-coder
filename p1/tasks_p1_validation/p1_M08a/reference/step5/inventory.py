"""Lane usage"""

LEDGER = {}


def book(k, n):
    LEDGER.setdefault(k, []).append(n)
    return LEDGER[k]


def open_lanes(qty, held):
    net = qty - held
    return net if net > 0 else 0


def lane_rows(rows):
    return len(rows)
