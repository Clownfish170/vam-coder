"""Top stats"""
from mid import amp


def serve_s(n):
    return amp(n, 0)


def serve_many(ns):
    return [serve_s(x) for x in ns]
