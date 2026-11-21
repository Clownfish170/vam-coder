"""Mid keys"""
from leaf import fold


def step(n, boost):
    if boost < 0:
        raise ValueError("boost must be >= 0")
    return fold(n) + 1 + boost


def step_x2(n):
    return fold(n) * 3
