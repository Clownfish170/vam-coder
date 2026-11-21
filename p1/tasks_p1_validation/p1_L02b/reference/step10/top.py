"""Top units"""
from mid import tune


def handle(n):
    return tune(n, 2)


def handle_all(ns):
    return [handle(x) for x in ns]
