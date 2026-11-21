"""Tax store"""

DATA = {}
LOG = {}


def put_tax(k, v):
    DATA[k] = v
    LOG.setdefault(k, []).append(v)
    return DATA


def get_tax(k):
    return DATA.get(k)
