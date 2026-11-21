"""Top cells"""
from mid import shift


def relay(n):
    return shift(n, 1)


def relay_all(ns):
    return [relay(x) for x in ns]
