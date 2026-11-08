"""Rate caps"""

LIMIT = 500


def under_cap(fee):
    return fee <= LIMIT
