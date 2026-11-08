"""Fee tier policies."""

BASE_FEE = 4


def tier(amount):
    if amount > 200:
        return "gold"
    if amount > 50:
        return "silver"
    return "basic"
