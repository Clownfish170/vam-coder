"""Top keys"""
from mid import step


def drive(n):
    return step(n, 0)


def drive_all(ns):
    return [drive(x) for x in ns]
