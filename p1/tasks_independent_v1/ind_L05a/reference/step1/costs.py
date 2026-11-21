"""Edge costs."""


EDGE_W = {}


def set_w(a, b, w):
    EDGE_W[(a, b)] = w
    EDGE_W[(b, a)] = w
