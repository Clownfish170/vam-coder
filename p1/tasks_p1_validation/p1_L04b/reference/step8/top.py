"""Top rows"""
from mid import align


def flush(n):
    return align(n, 0)


def flush_all(ns):
    return [flush(x) for x in ns]
