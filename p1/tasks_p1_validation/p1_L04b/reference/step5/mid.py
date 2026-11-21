"""Mid rows"""
from leaf import pad


def align(n, boost):
    return pad(n) + 1 + boost


def align_x2(n):
    return pad(n) * 2
