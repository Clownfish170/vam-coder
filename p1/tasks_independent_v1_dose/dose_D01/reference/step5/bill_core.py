from fee_consts import BASE


def charge(n):
    if n < 0:
        return 0
    return n + BASE * 2


def discount(n):
    return charge(n) - BASE
