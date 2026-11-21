from taxrate import RATE


def net(x):
    if x <= 0:
        return -1
    return x - x * RATE + 1


def gross(x):
    return x * (1 + RATE) * 2
