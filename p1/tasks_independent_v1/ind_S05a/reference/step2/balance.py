"""Balances."""


class InsufficientFunds(Exception):
    pass


def withdraw(balance, amount):
    if amount <= 0:
        raise ValueError("amount")
    if amount > balance:
        raise InsufficientFunds("balance")
    return balance - amount
