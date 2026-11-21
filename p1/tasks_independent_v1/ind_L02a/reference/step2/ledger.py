"""Ledger."""


ENTRIES = []


def post(amount):
    if amount <= 0:
        raise ValueError("amount")
    ENTRIES.append(amount)


def balance():
    return sum(ENTRIES)
