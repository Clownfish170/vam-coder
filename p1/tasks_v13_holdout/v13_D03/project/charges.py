"""Charge computation."""
from tiers import tier


def apply_fee(amount, fee):
    return amount + fee


def describe(amount):
    return tier(amount)
