"""Ledger."""


ENTRIES = []


def post(amount):
    ENTRIES.append(amount)
