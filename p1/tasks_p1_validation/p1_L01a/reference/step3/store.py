"""Fee store"""

DATA = {}
LOG = {}


def put(k, v):
    DATA[k] = v
    LOG.setdefault(k, []).append(v)
    return DATA


def get(k):
    return DATA.get(k)
