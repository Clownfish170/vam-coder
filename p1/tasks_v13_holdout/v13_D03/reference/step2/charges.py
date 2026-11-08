"""Charge computation."""
from tiers import tier, BASE_FEE


def apply_fee(amount, fee=None):
    if fee is None:
        fee = BASE_FEE
    return amount + fee


def describe(amount):
    return tier(amount)
