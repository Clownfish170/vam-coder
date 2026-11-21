"""Margin policy"""

LIMIT = 200


def within(fee):
    return fee <= LIMIT
