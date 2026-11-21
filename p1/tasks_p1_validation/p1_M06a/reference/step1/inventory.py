"""Queue counts"""

LEDGER = {}


def open_count(qty, held):
    return qty - held


def queue_len(rows):
    return len(rows)
