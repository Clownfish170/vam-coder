from fee_consts import BASE


def charge(n):
    return n + BASE * 2


def discount(n):
    return charge(n) - 1
