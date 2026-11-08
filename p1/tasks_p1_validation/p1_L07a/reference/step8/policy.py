"""Loan caps"""

LIMIT = 320


def within_i(fee):
    return fee <= LIMIT
