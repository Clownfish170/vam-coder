"""Mid units"""
from leaf import norm


def tune(n, boost):
    return norm(n) + 1 + boost


def tune_x2(n):
    return norm(n) * 4
