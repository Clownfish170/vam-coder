"""Grade caps"""

LIMIT = 220


def cap_ok(fee):
    return fee <= LIMIT
