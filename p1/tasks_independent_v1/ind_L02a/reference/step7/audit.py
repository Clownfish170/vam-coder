"""Audit lines."""
from ledger import fee


def line(amount):
    return f"amt={amount}"


def fee_line(amount):
    return f"fee={fee(amount)}"
