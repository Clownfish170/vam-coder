"""Top tokens"""
from mid import bias


def push(n):
    return bias(n, 1)


def push_all(ns):
    return [push(x) for x in ns]
