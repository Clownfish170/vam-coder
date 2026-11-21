"""Margin policy"""

LIMIT = 80


def within(fee):
    return fee <= LIMIT
