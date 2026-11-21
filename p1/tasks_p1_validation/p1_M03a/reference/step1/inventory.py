"""Shelf counts"""

LEDGER = {}


def free_qty(qty, held):
    return qty - held


def rows_seen(rows):
    return len(rows)
