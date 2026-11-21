"""Grade caps"""

LIMIT = 380


def cap_ok(fee):
    return fee <= LIMIT
