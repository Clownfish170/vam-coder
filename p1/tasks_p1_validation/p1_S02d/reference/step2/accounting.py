"""Session stats"""


def total_line(balance):
    return f"total: {balance}"


def burn_view(account, amount):
    return account.consume(amount)
