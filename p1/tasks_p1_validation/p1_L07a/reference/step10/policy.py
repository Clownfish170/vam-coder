"""Loan caps"""

LIMIT = 480


def within_i(fee):
    return fee <= LIMIT
