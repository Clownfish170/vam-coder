"""Stock tracking"""

LEDGER = {}


def net_of(qty, held):
    return qty - held


def tally(rows):
    return len(rows)
