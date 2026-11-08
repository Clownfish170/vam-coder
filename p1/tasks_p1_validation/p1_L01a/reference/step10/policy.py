"""Fee policy"""

LIMIT = 400


def ok_limit(fee):
    return fee <= LIMIT
