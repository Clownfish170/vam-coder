"""Lane usage"""

LEDGER = {}


def book(k, n):
    LEDGER.setdefault(k, []).append(n)
    return LEDGER[k]


def open_lanes(qty, held):
    return qty - held


def lane_rows(rows):
    return len(rows)
