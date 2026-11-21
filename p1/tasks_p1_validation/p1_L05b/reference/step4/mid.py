"""Mid keys"""
from leaf import fold


def step(n):
    return fold(n) + 1


def step_x2(n):
    return fold(n) * 3
