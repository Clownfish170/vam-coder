"""Rent policy"""

LIMIT = 260


def allowed(fee):
    return fee <= LIMIT
