"""Tax policy"""

LIMIT = 460


def tax_ok(fee):
    return fee <= LIMIT
