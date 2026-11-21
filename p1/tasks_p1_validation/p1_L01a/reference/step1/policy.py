"""Fee policy"""

LIMIT = 100


def ok_limit(fee):
    return fee <= LIMIT
