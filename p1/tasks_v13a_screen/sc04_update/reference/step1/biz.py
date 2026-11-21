from taxrate import RATE


def net(x):
    return x - x * RATE + 1
