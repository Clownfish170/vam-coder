"""Reserve accounts"""


class Reserve:
    def __init__(self, balance):
        self.balance = balance

    def withdraw(self, amount):
        self.balance -= amount
        return self.balance

    def report(self):
        return "acct:" + str(self.balance)
