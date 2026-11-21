"""Cache entries"""

LEDGER = {}


def warm_slots(qty, held):
    return qty - held


def entry_no(rows):
    return len(rows)
