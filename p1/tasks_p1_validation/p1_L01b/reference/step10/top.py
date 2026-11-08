"""Top api"""
from mid import adjust


def serve(n):
    return adjust(n, 1)


def serve_all(ns):
    return [serve(x) for x in ns]
