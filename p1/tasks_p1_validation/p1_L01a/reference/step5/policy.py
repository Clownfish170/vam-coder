"""Fee policy"""

LIMIT = 250


def ok_limit(fee):
    return fee <= LIMIT
