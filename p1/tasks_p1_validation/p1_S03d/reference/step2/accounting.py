"""Deposit reports"""


def total_line(balance):
    return f"total: {balance}"


def peek_view(account, amount):
    return account.takeout(amount)
