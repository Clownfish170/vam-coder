"""Session tokens"""


class Session:
    def __init__(self, balance):
        self.balance = balance

    def consume(self, amount):
        self.balance -= amount
        return self.balance

    def report(self):
        return "acct:" + str(self.balance)
