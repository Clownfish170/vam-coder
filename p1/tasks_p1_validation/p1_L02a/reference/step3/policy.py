"""Rate caps"""

LIMIT = 300


def under_cap(fee):
    return fee <= LIMIT
