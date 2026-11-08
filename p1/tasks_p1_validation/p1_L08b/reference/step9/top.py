"""Top frames"""
from mid import gate


def dispatch(n):
    return gate(n, 0)


def dispatch_all(ns):
    return [dispatch(x) for x in ns]
