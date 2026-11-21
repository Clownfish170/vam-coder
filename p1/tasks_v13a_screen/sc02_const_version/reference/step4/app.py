from config_consts import MARGIN


def price(x):
    return x * (1 + MARGIN) * 2


def fee(x):
    return x + MARGIN * 10


def total(xs):
    return sum(price(x) for x in xs)
