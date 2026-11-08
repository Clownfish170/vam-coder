"""Top frames"""
from mid import gate


def dispatch(n):
    return gate(n, 1)


def dispatch_all(ns):
    return [dispatch(x) for x in ns]
