"""Top tokens"""
from mid import bias


def push(n):
    return bias(n, 0)


def push_all(ns):
    return [push(x) for x in ns]
