"""Edge costs."""


EDGE_W = {}
DEFAULT_W = 5


def set_w(a, b, w):
    EDGE_W[(a, b)] = w
    EDGE_W[(b, a)] = w
