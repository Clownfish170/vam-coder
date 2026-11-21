"""Tax policy"""

LIMIT = 130


def tax_ok(fee):
    return fee <= LIMIT
