"""Inventory ledger"""

LEDGER = {}


def available(qty, held):
    return qty - held


def count_rows(rows):
    return len(rows)
