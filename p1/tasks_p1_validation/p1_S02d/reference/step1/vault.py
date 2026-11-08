"""Session tokens"""


class Session:
    def __init__(self, balance):
        self.balance = balance

    def consume(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        self.balance -= amount
        return self.balance

    def report(self):
        return "acct:" + str(self.balance)
