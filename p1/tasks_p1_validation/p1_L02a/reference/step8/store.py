"""Rate log"""

DATA = {}
LOG = {}


def save(k, v):
    DATA[k] = v
    LOG.setdefault(k, []).append(v)
    return DATA


def load(k):
    return DATA.get(k)


def blend(other):
    DATA.update(other)
    return DATA
