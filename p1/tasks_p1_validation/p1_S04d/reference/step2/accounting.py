"""Loan summaries"""


def total_line(balance):
    return f"total: {balance}"


def due_view(account, amount):
    return account.repay(amount)
