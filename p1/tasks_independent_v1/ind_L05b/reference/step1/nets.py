"""Edge-centric net."""


NODES = set()


LINKS = {}


def add_node(n):
    NODES.add(n)


def link(u, v):
    LINKS[(u, v)] = True
    LINKS[(v, u)] = True


def nodes():
    return sorted(NODES)
