"""Grade store"""

DATA = {}
LOG = {}


def put_row(k, v):
    DATA[k] = v
    LOG.setdefault(k, []).append(v)
    return DATA


def get_row(k):
    return DATA.get(k)
