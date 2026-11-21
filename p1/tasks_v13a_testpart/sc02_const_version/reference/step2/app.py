from config_consts import MARGIN


def price(x):
    return x * (1 + MARGIN)


def fee(x):
    return x + MARGIN * 10
