"""Bin levels"""

LEDGER = {}


def open_slots(qty, held):
    return qty - held


def bin_count(rows):
    return len(rows)
