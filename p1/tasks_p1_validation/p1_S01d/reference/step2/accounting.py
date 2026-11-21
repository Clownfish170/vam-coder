"""Reporting side"""


def total_line(balance):
    return f"total: {balance}"


def drain_view(account, amount):
    return account.withdraw(amount)
