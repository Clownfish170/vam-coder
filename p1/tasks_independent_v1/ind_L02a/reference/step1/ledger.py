"""Ledger."""


ENTRIES = []


def post(amount):
    ENTRIES.append(amount)


def balance():
    return sum(ENTRIES)
