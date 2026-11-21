from price_table import RATE, TAX


def quote(x):
    return x * RATE


def discount(x):
    return x - TAX


def total(x):
    return quote(x) + discount(x)
