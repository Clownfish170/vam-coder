"""Balances."""


def withdraw(balance, amount):
    if amount <= 0:
        raise ValueError("amount")
    return balance - amount
