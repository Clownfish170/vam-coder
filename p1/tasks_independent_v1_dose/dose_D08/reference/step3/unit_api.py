from unit_scale import SCALE, UNIT


def to_display(x):
    return (x * SCALE, UNIT)


def from_display(y):
    return y // SCALE
