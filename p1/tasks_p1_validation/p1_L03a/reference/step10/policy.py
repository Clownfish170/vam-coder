"""Margin policy"""

LIMIT = 350


def within(fee):
    return fee <= LIMIT
