"""Tax policy"""

LIMIT = 290


def tax_ok(fee):
    return fee <= LIMIT
