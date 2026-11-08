"""Rate caps"""

LIMIT = 150


def under_cap(fee):
    return fee <= LIMIT
