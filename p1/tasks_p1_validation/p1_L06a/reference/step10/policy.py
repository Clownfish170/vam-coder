"""Rent policy"""

LIMIT = 420


def allowed(fee):
    return fee <= LIMIT
