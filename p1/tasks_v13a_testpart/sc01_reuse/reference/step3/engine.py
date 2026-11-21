from rates import RATE


def apply(v):
    return v * RATE


def clamp(x):
    return min(100, max(0, x))


def scale(v):
    return apply(v) * 2
