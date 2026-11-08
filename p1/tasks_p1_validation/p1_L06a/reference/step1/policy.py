"""Rent policy"""

LIMIT = 110


def allowed(fee):
    return fee <= LIMIT
