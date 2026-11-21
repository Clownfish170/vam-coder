"""Ledger."""
import rates


ENTRIES = []


def post(amount):
    if amount <= 0:
        raise ValueError("amount")
    ENTRIES.append(amount)


def balance():
    return sum(ENTRIES)


def fee(amount):
    if amount <= rates.TIER1_LIMIT:
        return amount * rates.TIER1_RATE
    return amount * rates.TIER2_RATE


def window_total(n):
    if n <= 0:
        return 0
    return sum(ENTRIES[-n:])


def average():
    if not ENTRIES:
        return 0
    return sum(ENTRIES) / len(ENTRIES)
