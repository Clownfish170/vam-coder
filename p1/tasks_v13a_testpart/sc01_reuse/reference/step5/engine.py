from rates import RATE


def apply(v):
    if v < 0:
        return 0
    return v * RATE


def clamp(x):
    return min(100, max(0, x))


def scale(v):
    return apply(v) + 1
