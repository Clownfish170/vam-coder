"""Loan caps"""

LIMIT = 140


def within_i(fee):
    return fee <= LIMIT
