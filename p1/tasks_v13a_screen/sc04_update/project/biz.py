from taxrate import RATE


def net(x):
    return x * (1 - RATE)
