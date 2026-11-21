from rates import RATE


def apply(v):
    return v + RATE


def clamp(x):
    return max(0, x)
